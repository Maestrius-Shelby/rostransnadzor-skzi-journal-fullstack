"""
API роуты для работы с записями
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional
import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta

from ..services.parser_service import parser_service

router = APIRouter(tags=["records"])


@router.get("/records")
async def get_records(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Получить записи"""
    try:
        records = parser_service.get_records(limit, offset)
        return records
    except Exception as e:
        print(f"❌ Error in get_records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/count")
async def get_records_count():
    """Получить количество записей"""
    try:
        count = parser_service.get_records_count()
        return {
            "count": count,
            "new_count": parser_service.get_new_records_count(),
            "expiring_count": parser_service.get_expiring_records_count(),
            "expired_count": parser_service.get_expired_records_count()
        }
    except Exception as e:
        print(f"❌ Error in get_records_count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_data(request: dict):
    """Экспорт данных"""
    try:
        format = request.get("format", "excel")
        result = parser_service.export_records(format)
        
        # Если файл был открыт, добавляем флаг
        if isinstance(result, dict) and result.get('file_locked'):
            return {
                **result,
                "warning": True,
                "message": "Файл открыт в Excel. Закройте файл и повторите экспорт."
            }
        
        return result
    except Exception as e:
        print(f"❌ Error in export: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/records/import-excel")
async def import_excel(file: UploadFile = File(...)):
    """
    Импорт пользовательских полей из Excel файла.
    Поддерживает разные структуры Excel.
    """
    try:
        # Сохраняем загруженный файл
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        print(f"📖 Чтение Excel: {temp_path}")
        
        # Читаем Excel
        df = pd.read_excel(temp_path, header=0)
        print(f"📊 Прочитано строк (header=0): {len(df)}")
        print(f"📊 Колонки: {list(df.columns)}")
        
        # Показываем первые 3 строки для отладки
        print("\n📋 Первые 3 строки:")
        for i in range(min(3, len(df))):
            print(f"  Строка {i+1}: {dict(df.iloc[i])}")
        
        # ГИБКИЙ МАППИНГ КОЛОНОК
        column_mapping = {}
        
        for col in df.columns:
            col_clean = str(col).replace('\n', ' ').strip().lower()
            
            if any(name in col_clean for name in ['фио', 'фно', 'фіо', 'сотрудник', 'владелец']):
                column_mapping['fio'] = col
            elif any(name in col_clean for name in ['серийный', 'номер экземпляра', 'serial', 'инвентарный номер']):
                column_mapping['serial_number'] = col
            elif any(name in col_clean for name in ['дата установки', 'дата получения', 'date_from']):
                column_mapping['date_from'] = col
            elif any(name in col_clean for name in ['срок действия', 'дата сдачи', 'date_to']):
                column_mapping['date_to'] = col
            elif any(name in col_clean for name in ['тип ключа', 'тип', 'key_type']):
                column_mapping['key_type'] = col
            elif any(name in col_clean for name in ['носитель', 'флешки', 'key_carrier']):
                column_mapping['key_carrier_number'] = col
            elif any(name in col_clean for name in ['примечание', 'цель использования', 'основание']):
                if 'notes' not in column_mapping:
                    column_mapping['notes'] = col
            elif any(name in col_clean for name in ['скзи', 'информационные системы']):
                if 'skzi_type' not in column_mapping:
                    column_mapping['skzi_type'] = col
            elif any(name in col_clean for name in ['обслуживание']):
                if 'service_type' not in column_mapping:
                    column_mapping['service_type'] = col
        
        print(f"\n✅ Найденные колонки:")
        for field, col in column_mapping.items():
            print(f"  {field} -> {col}")
        
        # Если не найдены обязательные колонки - пытаемся создать их из доступных данных
        if 'fio' not in column_mapping and 'ФИО Сотрудника' in df.columns:
            column_mapping['fio'] = 'ФИО Сотрудника'
            print(f"  ✅ Используем 'ФИО Сотрудника' как fio")
        
        if 'serial_number' not in column_mapping:
            for col in df.columns:
                if 'номер' in str(col).lower():
                    column_mapping['serial_number'] = col
                    print(f"  ✅ Используем '{col}' как serial_number")
                    break
            if 'serial_number' not in column_mapping:
                print("  ⚠️ Серийный номер не найден, будет использован номер строки")
        
        if 'date_from' not in column_mapping and 'Дата получения ЭП' in df.columns:
            column_mapping['date_from'] = 'Дата получения ЭП'
            print(f"  ✅ Используем 'Дата получения ЭП' как date_from")
        
        if 'date_to' not in column_mapping and 'Дата сдачи ЭП' in df.columns:
            column_mapping['date_to'] = 'Дата сдачи ЭП'
            print(f"  ✅ Используем 'Дата сдачи ЭП' как date_to")
        
        required_fields = ['fio']
        missing = [f for f in required_fields if f not in column_mapping]
        if missing:
            print(f"❌ Отсутствуют обязательные колонки: {missing}")
            return {
                "message": f"Ошибка: не найдены обязательные колонки: {missing}",
                "updated_count": 0,
                "total_errors": 1,
                "errors": [f"Отсутствуют колонки: {missing}"],
                "found_columns": list(df.columns)
            }
        
        # Переименовываем колонки
        df_renamed = df.rename(columns={v: k for k, v in column_mapping.items()})
        
        # Добавляем недостающие колонки
        if 'serial_number' not in df_renamed.columns:
            df_renamed['serial_number'] = df_renamed.index + 1
        
        if 'date_from' not in df_renamed.columns:
            df_renamed['date_from'] = datetime.now().strftime('%d.%m.%Y, %H:%M')
        
        if 'date_to' not in df_renamed.columns:
            future = datetime.now() + timedelta(days=365)
            df_renamed['date_to'] = future.strftime('%d.%m.%Y, 23:59')
        
        if 'key_type' not in df_renamed.columns:
            df_renamed['key_type'] = 'ЭЦП'
        
        if 'key_carrier_number' not in df_renamed.columns:
            df_renamed['key_carrier_number'] = ''
        
        if 'skzi_type' not in df_renamed.columns:
            df_renamed['skzi_type'] = 'КриптоПро CSP 5.0'
        
        if 'service_type' not in df_renamed.columns:
            df_renamed['service_type'] = 'Установка ключевых документов'
        
        if 'destruction_date' not in df_renamed.columns:
            df_renamed['destruction_date'] = ''
        
        if 'destruction_signature' not in df_renamed.columns:
            df_renamed['destruction_signature'] = ''
        
        if 'notes' not in df_renamed.columns:
            df_renamed['notes'] = ''
        
        # Преобразуем все в строки и очищаем
        for col in df_renamed.columns:
            df_renamed[col] = df_renamed[col].astype(str).str.strip()
            df_renamed[col] = df_renamed[col].replace('nan', '')
            df_renamed[col] = df_renamed[col].replace('None', '')
            df_renamed[col] = df_renamed[col].replace('—', '')
        
        # Удаляем пустые строки
        df_renamed['_empty'] = df_renamed.apply(lambda row: all(row[col] == '' for col in df_renamed.columns if col != '_empty'), axis=1)
        df_renamed = df_renamed[~df_renamed['_empty']]
        df_renamed = df_renamed.drop(columns=['_empty'])
        
        # Заменяем пустые значения
        if 'fio' in df_renamed.columns:
            df_renamed['fio'] = df_renamed['fio'].replace('', 'Неизвестно')
        
        if 'serial_number' in df_renamed.columns:
            df_renamed['serial_number'] = df_renamed['serial_number'].replace('', str(df_renamed.index[0] + 1) if len(df_renamed) > 0 else '1')
        
        print(f"\n📊 После очистки: {len(df_renamed)} строк")
        
        if df_renamed.empty:
            print("❌ Данные не найдены в Excel")
            return {
                "message": "Файл не содержит данных после очистки",
                "updated_count": 0,
                "total_errors": 0,
                "errors": ["Файл пуст или имеет неправильную структуру"]
            }
        
        # ✅ Преобразуем в записи (СОХРАНЯЕМ ВРЕМЯ!)
        records = []
        for idx, row in df_renamed.iterrows():
            # ✅ НЕ обрезаем время!
            date_from = str(row.get('date_from', '')).strip()
            date_to = str(row.get('date_to', '')).strip()
            
            # Если дата пустая - ставим дефолт с временем
            if date_from == '' or date_from == '—' or date_from == 'nan':
                date_from = datetime.now().strftime('%d.%m.%Y, %H:%M')
            if date_to == '' or date_to == '—' or date_to == 'nan':
                future = datetime.now() + timedelta(days=365)
                date_to = future.strftime('%d.%m.%Y, 23:59')
            
            # ✅ Если в дате нет времени - добавляем его
            if ', ' not in date_from:
                date_from = date_from + ', 00:00'
            if ', ' not in date_to:
                date_to = date_to + ', 23:59'
            
            record = {
                'id': idx + 1,
                'fio': str(row.get('fio', 'Неизвестно')).strip(),
                'serial_number': str(row.get('serial_number', f'SN-{idx+1}')).strip(),
                'date_from': date_from,  # ← сохраняем с временем
                'date_to': date_to,      # ← сохраняем с временем
                'key_type': str(row.get('key_type', 'ЭЦП')).strip(),
                'key_carrier_number': str(row.get('key_carrier_number', '')).strip(),
                'skzi_type': str(row.get('skzi_type', 'КриптоПро CSP 5.0')).strip(),
                'service_type': str(row.get('service_type', 'Установка ключевых документов')).strip(),
                'destruction_date': str(row.get('destruction_date', '')).strip(),
                'destruction_signature': str(row.get('destruction_signature', '')).strip(),
                'notes': str(row.get('notes', '')).strip()
            }
            
            records.append(record)
        
        print(f"✅ Загружено {len(records)} записей")
        
        # Если есть записи - обновляем
        if records:
            existing_records = parser_service.records or []
            
            # Обновляем или добавляем
            for new_record in records:
                found = False
                for i, existing in enumerate(existing_records):
                    if (existing.get('fio', '').strip() == new_record['fio'] and
                        existing.get('serial_number', '').strip() == new_record['serial_number']):
                        existing_records[i] = new_record
                        found = True
                        break
                if not found:
                    existing_records.append(new_record)
            
            parser_service.records = existing_records
            parser_service.total_records = len(existing_records)
            
            # Сохраняем
            parser_service._save_records()
            
            # Экспортируем в Excel
            try:
                parser_service._export_to_fixed_excel()
                print("✅ Excel экспортирован")
            except Exception as e:
                print(f"⚠️ Ошибка экспорта Excel: {e}")
        
        # Удаляем временный файл
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        return {
            "message": f"Импорт завершен. Загружено записей: {len(records)}",
            "updated_count": len(records),
            "total_records": len(parser_service.records),
            "errors": [],
            "total_errors": 0
        }
        
    except Exception as e:
        print(f"❌ Error in import_excel: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/records/{record_index}")
async def update_record_fields(record_index: int, fields: dict):
    """
    Обновить пользовательские поля записи по индексу.
    """
    try:
        if record_index < 0 or record_index >= len(parser_service.records):
            raise HTTPException(status_code=404, detail="Запись не найдена")
        
        allowed_fields = [
            'key_carrier_number',
            'destruction_date',
            'destruction_signature',
            'notes'
        ]
        
        record = parser_service.records[record_index]
        
        for field, value in fields.items():
            if field in allowed_fields:
                record[field] = value
        
        parser_service._save_records()
        
        return {
            "message": "Запись обновлена",
            "record_index": record_index,
            "updated_fields": list(fields.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in update_record_fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/clear")
async def clear_all_records():
    """Очистить все записи"""
    try:
        parser_service.records = []
        parser_service.total_records = 0
        parser_service.current_record = 0
        parser_service.progress = 0
        parser_service._save_records()
        parser_service._export_to_fixed_excel()
        
        print("🗑️ Все записи очищены")
        return {
            "message": "Все записи успешно удалены",
            "count": 0,
            "status": "success"
        }
    except Exception as e:
        print(f"❌ Error in clear_all_records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/records/delete")
async def delete_records(request: dict):
    """Удалить выбранные записи"""
    try:
        ids = request.get("ids", [])
        if not ids:
            raise HTTPException(status_code=400, detail="No records specified")
        
        records_to_keep = []
        for i, record in enumerate(parser_service.records):
            if i not in ids:
                records_to_keep.append(record)
        
        parser_service.records = records_to_keep
        parser_service.total_records = len(records_to_keep)
        parser_service._save_records()
        parser_service._export_to_fixed_excel()
        
        return {
            "message": f"Удалено {len(ids)} записей",
            "count": len(records_to_keep),
            "records": parser_service.records
        }
    except Exception as e:
        print(f"❌ Error in delete_records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/download")
async def download_file(path: str):
    """Скачать файл"""
    from fastapi.responses import FileResponse
    import os
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(path)
    
    return FileResponse(
        path,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=filename
    )