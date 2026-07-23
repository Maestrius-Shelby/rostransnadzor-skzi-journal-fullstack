
# Полный пиздец - ломает весь поток
# import os
# import time
# import hashlib
# from pathlib import Path
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
# from typing import Optional, Callable
# from datetime import datetime
# import threading

# from .excel_handler import ExcelHandler
# from .websocket_server import WebSocketManager
# import asyncio

# class ExcelFileHandler(FileSystemEventHandler):
#     """Обработчик событий файловой системы для Excel файлов"""
    
#     def __init__(self, watcher_service):
#         self.watcher_service = watcher_service
#         self.last_modified = 0
#         self.cooldown = 2  # Задержка между обработками (сек)
        
#     def on_modified(self, event):
#         """Вызывается при изменении файла"""
#         if event.is_directory:
#             return
            
#         # Проверяем расширение файла
#         file_path = event.src_path
#         if not (file_path.endswith('.xlsx') or file_path.endswith('.xls')):
#             return
            
#         # Проверяем что это не временный файл
#         if '~$' in file_path or '.~lock.' in file_path:
#             return
            
#         # Защита от множественных событий
#         current_time = time.time()
#         if current_time - self.last_modified < self.cooldown:
#             return
            
#         self.last_modified = current_time
#         print(f"\n📝 Обнаружено изменение: {os.path.basename(file_path)}")
#         self.watcher_service.process_excel_file(file_path)


# class ExcelWatcherService:
#     """Сервис наблюдения за Excel файлами"""
    
#     def __init__(
#         self,
#         data_manager=None,
#         watch_paths: list = None,
#         json_output_path: str = None,
#         ws_host: str = 'localhost',
#         ws_port: int = 8765
#     ):
#         self.data_manager = data_manager
#         self.watch_paths = watch_paths or []
#         self.json_output_path = json_output_path or 'data/records.json'
        
#         # Компоненты
#         self.excel_handler = ExcelHandler(data_manager)
#         self.ws_manager = WebSocketManager(ws_host, ws_port)
#         self.observer = None
#         self.is_running = False
        
#         # Статистика
#         self.stats = {
#             'files_processed': 0,
#             'last_update': None,
#             'errors': 0
#         }
        
#     def add_watch_path(self, path: str):
#         """Добавить путь для наблюдения"""
#         if path not in self.watch_paths:
#             self.watch_paths.append(path)
            
#     def process_excel_file(self, file_path: str):
#         """Обработать Excel файл"""
#         try:
#             print(f"📄 Обработка файла: {file_path}")
            
#             # Читаем Excel
#             data = self.excel_handler.read_excel(file_path)
            
#             if data:
#                 # Сохраняем JSON
#                 self.excel_handler.save_json(data, self.json_output_path)
                
#                 # Отправляем через WebSocket
#                 asyncio.run(self.ws_manager.broadcast({
#                     'type': 'excel_updated',
#                     'data': data,
#                     'timestamp': datetime.now().isoformat()
#                 }))
                
#                 self.stats['files_processed'] += 1
#                 self.stats['last_update'] = datetime.now().isoformat()
                
#                 print(f"✅ Обработано {data['total']} записей")
                
#         except Exception as e:
#             self.stats['errors'] += 1
#             print(f"❌ Ошибка обработки {file_path}: {e}")
    
#     def start(self):
#         """Запустить вотчер"""
#         print("=" * 60)
#         print("🚀 ЗАПУСК СЕРВИСА НАБЛЮДЕНИЯ ЗА EXCEL")
#         print("=" * 60)
        
#         self.is_running = True
        
#         # Запускаем WebSocket сервер в отдельном потоке
#         ws_thread = threading.Thread(
#             target=self._run_websocket_server,
#             daemon=True
#         )
#         ws_thread.start()
        
#         # Запускаем файловый вотчер
#         if self.watch_paths:
#             self._start_file_watcher()
#         else:
#             print("⚠️ Нет путей для наблюдения")
    
#     def _run_websocket_server(self):
#         """Запустить WebSocket сервер"""
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
        
#         try:
#             loop.run_until_complete(self.ws_manager.start_server())
#             loop.run_forever()
#         except Exception as e:
#             print(f"❌ Ошибка WebSocket сервера: {e}")
#         finally:
#             loop.close()
    
#     def _start_file_watcher(self):
#         """Запустить наблюдение за файлами"""
#         self.observer = Observer()
        
#         for path in self.watch_paths:
#             if os.path.isfile(path):
#                 watch_dir = os.path.dirname(path) or '.'
#             else:
#                 watch_dir = path
                
#             self.observer.schedule(
#                 ExcelFileHandler(self),
#                 watch_dir,
#                 recursive=False
#             )
#             print(f"👁️ Наблюдение: {watch_dir}")
        
#         self.observer.start()
#         print("✅ Вотчер запущен\n")
        
#         try:
#             while self.is_running:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             self.stop()
    
#     def stop(self):
#         """Остановить вотчер"""
#         print("\n🛑 Остановка сервиса...")
#         self.is_running = False
        
#         if self.observer:
#             self.observer.stop()
#             self.observer.join()
            
#         print("👋 Сервис остановлен")
    
#     def get_stats(self) -> dict:
#         """Получить статистику работы"""
#         return {
#             **self.stats,
#             'is_running': self.is_running,
#             'watch_paths': self.watch_paths,
#             'ws_clients': len(self.ws_manager.clients)
#         }


import os
import time
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Optional, Callable
from datetime import datetime
import threading
import asyncio

from .excel_handler import ExcelHandler
from .websocket_server import WebSocketManager


class ExcelFileHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы для Excel файлов"""
    
    def __init__(self, watcher_service):
        self.watcher_service = watcher_service
        self.last_modified = 0
        self.cooldown = 2
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        if not (file_path.endswith('.xlsx') or file_path.endswith('.xls')):
            return
            
        if '~$' in file_path or '.~lock.' in file_path:
            return
            
        current_time = time.time()
        if current_time - self.last_modified < self.cooldown:
            return
            
        self.last_modified = current_time
        print(f"\n📝 Обнаружено изменение: {os.path.basename(file_path)}")
        self.watcher_service.process_excel_file(file_path)


class ExcelWatcherService:
    """Сервис наблюдения за Excel файлами"""
    
    def __init__(
        self,
        data_manager=None,
        watch_paths: list = None,
        json_output_path: str = None,
        ws_host: str = 'localhost',
        ws_port: int = 8765
    ):
        self.data_manager = data_manager
        self.watch_paths = watch_paths or []
        self.json_output_path = json_output_path or 'src/data/records.json'
        
        self.excel_handler = ExcelHandler(data_manager)
        self.ws_manager = WebSocketManager(ws_host, ws_port)
        self.observer = None
        self.is_running = False
        self.watcher_thread = None
        
        self.stats = {
            'files_processed': 0,
            'last_update': None,
            'errors': 0
        }
        
    def add_watch_path(self, path: str):
        if path not in self.watch_paths:
            self.watch_paths.append(path)
            
    def process_excel_file(self, file_path: str):
        try:
            print(f"📄 Обработка файла: {file_path}")
            data = self.excel_handler.read_excel(file_path)
            
            if data:
                self.excel_handler.save_json(data, self.json_output_path)
                
                # Отправляем через WebSocket (в отдельном потоке)
                asyncio.run_coroutine_threadsafe(
                    self.ws_manager.broadcast({
                        'type': 'excel_updated',
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }),
                    asyncio.get_event_loop()
                )
                
                self.stats['files_processed'] += 1
                self.stats['last_update'] = datetime.now().isoformat()
                print(f"✅ Обработано {data['total']} записей")
                
        except Exception as e:
            self.stats['errors'] += 1
            print(f"❌ Ошибка обработки {file_path}: {e}")
    
    def start(self):
        """Запустить вотчер (неблокирующий)"""
        print("=" * 60)
        print("🚀 ЗАПУСК СЕРВИСА НАБЛЮДЕНИЯ ЗА EXCEL")
        print("=" * 60)
        
        self.is_running = True
        
        # Запускаем WebSocket сервер в отдельном потоке
        ws_thread = threading.Thread(
            target=self._run_websocket_server,
            daemon=True
        )
        ws_thread.start()
        
        # Запускаем файловый вотчер в отдельном потоке
        if self.watch_paths:
            self.watcher_thread = threading.Thread(
                target=self._run_file_watcher,
                daemon=True
            )
            self.watcher_thread.start()
            print("✅ Вотчер запущен в фоновом режиме")
        else:
            print("⚠️ Нет путей для наблюдения")
    
    def _run_websocket_server(self):
        """Запустить WebSocket сервер"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.ws_manager.start_server())
            loop.run_forever()
        except Exception as e:
            print(f"❌ Ошибка WebSocket сервера: {e}")
        finally:
            loop.close()
    
    def _run_file_watcher(self):
        """Запустить наблюдение за файлами в отдельном потоке"""
        self.observer = Observer()
        
        for path in self.watch_paths:
            if os.path.isfile(path):
                watch_dir = os.path.dirname(path) or '.'
            else:
                watch_dir = path
                
            self.observer.schedule(
                ExcelFileHandler(self),
                watch_dir,
                recursive=False
            )
            print(f"👁️ Наблюдение: {watch_dir}")
        
        self.observer.start()
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Остановить вотчер"""
        print("\n🛑 Остановка сервиса...")
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        print("👋 Сервис остановлен")
    
    def get_stats(self) -> dict:
        return {
            **self.stats,
            'is_running': self.is_running,
            'watch_paths': self.watch_paths,
            'ws_clients': len(self.ws_manager.clients)
        }