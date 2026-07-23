"""
FastAPI приложение
"""
import json
import os
import asyncio
import threading
import time
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .routes.parser import router as parser_router
from .routes.records import router as records_router
from .routes.settings import router as settings_router
from .routes.history import router as history_router
from .routes.auth import router as auth_router, get_current_user
from .services.parser_service import parser_service
from ..utils.logger import setup_logger

setup_logger()

# ============================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================
_watcher = None
_watcher_thread = None
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_backend_dir():
    return _backend_dir

def find_latest_excel():
    """Найти Excel-файл Журнал_СКЗИ.xlsx в output/"""
    output_dir = os.path.join(_backend_dir, 'output')
    
    # Ищем конкретный файл
    excel_path = os.path.join(output_dir, 'Журнал_СКЗИ.xlsx')
    
    if os.path.exists(excel_path):
        print(f"📊 Найден Excel: Журнал_СКЗИ.xlsx")
        return excel_path
    
    # Запасной вариант — любой xlsx
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            if f.endswith('.xlsx') and not f.startswith('~$'):
                full_path = os.path.join(output_dir, f)
                print(f"📊 Найден Excel: {f}")
                return full_path
    
    print(f"⚠️ Excel файлы не найдены в: {output_dir}")
    return None

def sync_excel_to_json():
    """Синхронизировать ТОЛЬКО пользовательские поля из Excel → JSON"""
    excel_file = find_latest_excel()
    if not excel_file:
        return False
    
    try:
        import pandas as pd
        
        df = pd.read_excel(excel_file, sheet_name='СКЗИ')
        df = df.fillna('')
        
        updated_count = 0
        
        for _, row in df.iterrows():
            excel_fio = str(row.iloc[4]).strip() if len(row) > 4 else ''
            serial = str(row.iloc[7]).strip() if len(row) > 7 else ''
            
            def clean_value(val):
                if val is None or val == '' or pd.isna(val):
                    return ''
                if isinstance(val, float):
                    if val == int(val):
                        return str(int(val))
                    return str(val).rstrip('0').rstrip('.')
                return str(val).strip()
            
            carrier = clean_value(row.iloc[8]) if len(row) > 8 else ''
            dest_date = clean_value(row.iloc[9]) if len(row) > 9 else ''
            dest_sign = clean_value(row.iloc[10]) if len(row) > 10 else ''
            notes = clean_value(row.iloc[11]) if len(row) > 11 else ''
            
            if not excel_fio:
                continue
            
            for record in parser_service.records:
                if record.get('fio', '').strip() == excel_fio:
                    if serial and record.get('serial_number', '').strip() != serial:
                        continue
                    
                    # Всегда обновляем поля (даже пустыми)
                    record['key_carrier_number'] = carrier
                    record['destruction_date'] = dest_date
                    record['destruction_signature'] = dest_sign
                    record['notes'] = notes
                    updated_count += 1
                    break
        
        parser_service._save_records()
        
        print(f"🔄 Обновлено {updated_count} пользовательских полей из Excel")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_watcher_loop(excel_path: str, json_path: str):
    """Фоновый поток: отслеживает изменения Excel и синхронизирует"""
    import hashlib
    
    print(f"👁️ Вотчер запущен для: {os.path.basename(excel_path)}")
    
    last_hash = None
    update_flag_file = os.path.join(_backend_dir, 'data', '.excel_updated')
    
    while True:
        try:
            if os.path.exists(excel_path):
                with open(excel_path, 'rb') as f:
                    current_hash = hashlib.md5(f.read()).hexdigest()
                
                if last_hash and current_hash != last_hash:
                    print(f"\n📝 Изменения обнаружены в {os.path.basename(excel_path)}")
                    
                    if sync_excel_to_json():
                        # Создаем файл-флаг обновления
                        try:
                            os.makedirs(os.path.dirname(update_flag_file), exist_ok=True)
                            with open(update_flag_file, 'w') as f:
                                f.write(str(time.time()))
                            print("📡 Флаг обновления установлен")
                        except Exception as e:
                            print(f"⚠️ Ошибка создания флага: {e}")
                
                last_hash = current_hash
            
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Ошибка вотчера: {e}")
            time.sleep(5)

# ============================================
# LIFESPAN
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _watcher_thread
    
    print("🚀 Запуск API сервера...")
    print("📊 Загружено записей:", len(parser_service.records))
    print("🟢 Новых:", parser_service.get_new_records_count())
    print("🟠 Истекают:", parser_service.get_expiring_records_count())
    
    # Запуск вотчера в фоновом потоке
    excel_file = find_latest_excel()
    
    if excel_file:
        json_path = os.path.join(_backend_dir, 'src', 'data', 'records.json')
        
        _watcher_thread = threading.Thread(
            target=run_watcher_loop,
            args=(excel_file, json_path),
            daemon=True
        )
        _watcher_thread.start()
        print(f"✅ Вотчер запущен: {os.path.basename(excel_file)}")
    else:
        print("⚠️ Excel файл не найден в output/. Вотчер не запущен.")
    
    yield
    
    print("🛑 API сервер остановлен")


app = FastAPI(
    title="Росказна Парсер API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    # ============================================
    # РАЗРЕШЁННЫЕ ОРИГИНЫ (откуда можно делать запросы)
    # ============================================
    allow_origins=[
        # --- ФРОНТЕНД В РАЗРАБОТКЕ ---
        "http://localhost:5173",      # Vite dev сервер (основной порт)
        "http://127.0.0.1:5173",       # Vite dev через localhost IP
        "http://localhost:4173",      # Vite preview сервер (проверка сборки)
        "http://127.0.0.1:4173",      # Vite preview через IP
        
        # --- ДРУГИЕ ФРОНТЕНДЫ ---
        "http://localhost:3000",       # Альтернативный фронтенд (React CRA, Next.js)
        "http://127.0.0.1:3000",       # Альтернативный фронтенд через IP
        
        # --- ПРОДАКШН (добавить при деплое) ---
        # "https://yourdomain.com",    # Продакшн домен (заменить на свой)
        # "https://www.yourdomain.com",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

app.include_router(parser_router, prefix="/api")
app.include_router(records_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


# ============================================
# ЭНДПОИНТЫ ВОТЧЕРА
# ============================================
@app.post("/api/watcher/sync")
async def sync_now():
    """Принудительная синхронизация"""
    success = sync_excel_to_json()
    if success:
        return {"status": "ok", "records": len(parser_service.records)}
    return {"status": "error"}


@app.get("/api/watcher/status")
async def watcher_status():
    excel_file = find_latest_excel()
    return {
        "running": _watcher_thread is not None and _watcher_thread.is_alive(),
        "excel_file": os.path.basename(excel_file) if excel_file else None,
        "records": len(parser_service.records)
    }


# ============================================
# WEBSOCKET
# ============================================
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    parser_service.add_subscriber(websocket)
    
    # Файл-флаг обновления
    update_flag_file = os.path.join(_backend_dir, 'data', '.excel_updated')
    last_update_time = 0
    
    try:
        # Отправляем начальный статус (без records — слишком большой объем)
        status = parser_service.get_status()
        status.pop('records', None)  # Не отправляем records через WebSocket
        status["watcher"] = {
            "running": _watcher_thread is not None and _watcher_thread.is_alive(),
            "excel_file": os.path.basename(find_latest_excel()) if find_latest_excel() else None
        }
        await websocket.send_json(status)
        
        while True:
            try:
                # Проверяем флаг обновления Excel
                if os.path.exists(update_flag_file):
                    with open(update_flag_file, 'r') as f:
                        flag_time = float(f.read().strip())
                    
                    if flag_time > last_update_time:
                        last_update_time = flag_time
                        await websocket.send_json({
                            "type": "excel_updated",
                            "message": "Данные обновлены из Excel",
                            "total": len(parser_service.records)
                        })
                
                # Ждем сообщения от клиента
                data = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
                if data:
                    try:
                        command = json.loads(data)
                        if command.get("command") == "ping":
                            await websocket.send_json({"type": "pong"})
                        elif command.get("command") == "sync":
                            success = sync_excel_to_json()
                            await websocket.send_json({
                                "type": "sync_result",
                                "success": success,
                                "total": len(parser_service.records)
                            })
                    except json.JSONDecodeError:
                        pass
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
            
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")
    finally:
        parser_service.remove_subscriber(websocket)


@app.get("/")
async def root():
    return {"message": "Росказна Парсер API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)