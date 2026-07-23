"""
Сервис для управления парсером
"""
import asyncio
import time
import json
import os
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import random
import hashlib

from ...export.excel_exporter import ExcelExporter, is_file_locked
from ..models.schemas import ParserStatus, ParserStatusResponse, Record


class ParserService:
    """Сервис для управления парсером"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Состояние парсера
        self.status = "idle"
        self.progress = 0
        self.total_records = 0
        self.current_record = 0
        self.message = None
        self.records = []
        self.is_running = False
        self.should_stop = False
        self.started_at = None
        self.completed_at = None
        self.last_files = {}
        
        # Подписчики на обновления (WebSocket)
        self.subscribers = []
        
        # Путь к файлу с данными
        self.data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'records.json'
        )
        self._ensure_data_dir()
        
        # Загружаем сохраненные записи
        self._load_records()
        
        # Запускаем ежедневный парсинг (отложенно)
        self._daily_task = None
        self._daily_task_started = False
        # self._schedule_daily_parser()
        
        # Запускаем автообновление флагов
        self._auto_update_task = None
        self._auto_update_started = False
        self._start_auto_update_flags()
    
    def _ensure_data_dir(self):
        """Создать директорию для данных если её нет"""
        data_dir = os.path.dirname(self.data_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _load_records(self):
        """Загрузить записи из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = data.get('records', [])
                    
                    # Обновляем ТОЛЬКО флаги истечения (is_expiring, days_left)
                    # НЕ трогаем is_new и is_expired — они сохранены из прошлого сравнения
                    today = datetime.now().date()
                    for record in self.records:
                        if record.get('date_to'):
                            try:
                                date_to_str = record['date_to']
                                if ', ' in date_to_str:
                                    date_to_str = date_to_str.split(', ')[0]
                                date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                                days_left = (date_to - today).days
                                record['days_left'] = days_left
                                
                                # is_expiring только если не is_expired
                                if not record.get('is_expired'):
                                    record['is_expiring'] = 0 <= days_left <= 15
                                else:
                                    record['is_expiring'] = False
                            except:
                                pass
                        
                        # Убеждаемся что is_mock существует
                        if 'is_mock' not in record:
                            record['is_mock'] = False
                    
                    print(f"📂 Загружено {len(self.records)} записей из файла")
                    print(f"   🆕 Новых: {len([r for r in self.records if r.get('is_new')])}")
                    print(f"   🟠 Истекающих: {len([r for r in self.records if r.get('is_expiring')])}")
                    print(f"   🔴 Истекших: {len([r for r in self.records if r.get('is_expired')])}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка загрузки данных: {e}")
                self.records = []
        else:
            self.records = []
    
    def _save_records(self):
        """Сохранить записи в файл"""
        try:
            data = {
                'records': self.records,
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.records)
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Сохранено {len(self.records)} записей в {self.data_file}")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения данных: {e}")
    
    def _get_record_hash(self, record: Dict) -> str:
        """
        Получить криптографический хеш записи для сравнения.
        Использует ключевые поля: fio, serial_number, date_from, date_to
        """
        key_fields = ['fio', 'serial_number', 'date_from', 'date_to']
        key_string = '|'.join(str(record.get(field, '')) for field in key_fields)
        return hashlib.sha256(key_string.encode('utf-8')).hexdigest()
    
    def _start_auto_update_flags(self):
        """Запустить автоматическое обновление флагов"""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._auto_update_flags())
            self._auto_update_started = True
            print("✅ Автообновление флагов запущено")
        except RuntimeError:
            # Если нет running loop - сохраняем задачу для запуска позже
            self._auto_update_task = self._auto_update_flags
            print("⏳ Автообновление флагов будет запущено при старте API")

    def start_auto_update_flags(self):
        """Запустить автообновление флагов (вызывается при старте API)"""
        if hasattr(self, '_auto_update_task') and self._auto_update_task and not self._auto_update_started:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._auto_update_task())
                self._auto_update_started = True
                print("✅ Автообновление флагов запущено")
            except RuntimeError:
                print("⚠️ Нет running loop для запуска автообновления флагов")

    async def _auto_update_flags(self):
        """
        Автоматическое обновление флагов истечения каждую минуту.
        """
        while True:
            try:
                await asyncio.sleep(60)  # Каждую минуту
                
                # Проверяем, изменились ли флаги
                old_expired = self.get_expired_records_count()
                old_expiring = self.get_expiring_records_count()
                
                # Обновляем флаги
                self._update_record_flags()
                
                # Проверяем, изменилось ли что-то
                new_expired = self.get_expired_records_count()
                new_expiring = self.get_expiring_records_count()
                
                if old_expired != new_expired or old_expiring != new_expiring:
                    # Сохраняем изменения
                    self._save_records()
                    # Уведомляем подписчиков
                    await self._update_status()
                    print(f"🔄 Флаги обновлены: истекших {old_expired}->{new_expired}, истекающих {old_expiring}->{new_expiring}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка обновления флагов: {e}")
                await asyncio.sleep(60)  # Ждем минуту и пробуем снова

    def _update_record_flags(self):
        """
        Обновить флаги записей (is_expiring, days_left).
        
        Логика:
        - days_left = количество дней до date_to (с учетом времени)
        - is_expiring = True если 0 <= days_left <= 15
        - Если days_left < 0 — срок истёк (is_expired = True)
        - Если сегодня и время уже прошло — тоже истекло
        """
        from datetime import datetime
        
        now = datetime.now()
        today = now.date()
        
        for record in self.records:
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to']
                    
                    # Парсим дату и время
                    if ', ' in date_to_str:
                        date_part, time_part = date_to_str.split(', ')
                        date_to = datetime.strptime(date_part, '%d.%m.%Y').date()
                        
                        # Парсим время
                        try:
                            time_to = datetime.strptime(time_part, '%H:%M').time()
                            # Объединяем дату и время
                            date_to_datetime = datetime.combine(date_to, time_to)
                        except ValueError:
                            # Если время не распарсилось - считаем полночь
                            date_to_datetime = datetime.combine(date_to, datetime.min.time())
                    else:
                        # Если нет времени - считаем полночь
                        date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                        date_to_datetime = datetime.combine(date_to, datetime.min.time())
                    
                    # ✅ Сравниваем с текущим моментом (дата + время)
                    # Если время уже прошло сегодня — считаем истекшим
                    if date_to_datetime < now:
                        days_left = -1
                    else:
                        # Округляем вниз до целых дней
                        days_left = (date_to_datetime.date() - today).days
                    
                    record['days_left'] = days_left
                    
                    # ✅ is_expiring = True только если осталось 0-15 дней И время еще не прошло
                    record['is_expiring'] = 0 <= days_left <= 15
                    
                    # ✅ Если days_left < 0 — запись истекла
                    if days_left < 0:
                        record['is_expired'] = True
                        record['is_expiring'] = False
                    
                except Exception as e:
                    print(f"⚠️ Ошибка парсинга даты {record.get('date_to')}: {e}")
                    record['is_expiring'] = False
                    record['days_left'] = None
                
    def _compare_and_update_records(self, old_records: List[Dict], new_records: List[Dict]):
        """
        Сравнивает старый и новый списки записей по крипто-хешу.
        
        Логика:
        - Если старых записей нет (первый парсинг) → все новые записи получают is_new=True
        - Записи из old_records, которых нет в new_records → помечаются is_expired=True (красные)
        - Записи из new_records, которых нет в old_records → помечаются is_new=True (зеленые)
        - Записи, которые есть в обоих списках → обновляют ТОЛЬКО системные поля,
        пользовательские поля сохраняются из старой записи
        
        Пользовательские поля (не перезаписываются при парсинге):
        - key_carrier_number (Номер разового ключевого носителя)
        - destruction_date (Отметка об уничтожении - Дата)
        - destruction_signature (Отметка об уничтожении - Подпись)
        - notes (Примечание)
        """
        # Поля, которые может редактировать пользователь — их нельзя перезаписывать
        USER_EDITABLE_FIELDS = [
            'key_carrier_number',      # Номер разового ключевого носителя или зоны СКЗИ
            'destruction_date',        # Отметка об уничтожении - Дата
            'destruction_signature',   # Отметка об уничтожении - Подпись
            'notes'                    # Примечание
        ]
        
        # Системные поля, которые управляются парсером
        SYSTEM_FIELDS = [
            'is_new', 'is_expired', 'is_expiring', 
            'days_left', 'is_mock', 'added_at', '_found_in_new'
        ]
        
        # Если старых записей нет (первый парсинг) — все записи новые
        if not old_records:
            for rec in new_records:
                rec['is_new'] = True
                rec['is_expired'] = False
                rec['is_mock'] = False
            self.records = new_records
            print(f"📊 Первый парсинг: все {len(new_records)} записей помечены как новые")
            return
        
        # Строим словари хеш -> запись для быстрого поиска
        old_hash_map = {self._get_record_hash(r): r for r in old_records}
        new_hash_map = {self._get_record_hash(r): r for r in new_records}
        
        old_hashes = set(old_hash_map.keys())
        new_hashes = set(new_hash_map.keys())
        
        # Хеши записей по категориям
        common_hashes = old_hashes & new_hashes       # Есть в обоих
        expired_hashes = old_hashes - new_hashes       # Только в старом (истекшие)
        new_only_hashes = new_hashes - old_hashes      # Только в новом (новые)
        
        print(f"📊 Сравнение записей:")
        print(f"   📝 Общие (обновлены): {len(common_hashes)}")
        print(f"   🔴 Истекшие (удалены с сайта): {len(expired_hashes)}")
        print(f"   🟢 Новые (появились на сайте): {len(new_only_hashes)}")
        
        updated_records = []
        
        # 1. Обрабатываем общие записи
        for h in common_hashes:
            old_rec = old_hash_map[h]
            new_rec = new_hash_map[h]
            
            # Обновляем ТОЛЬКО поля, которые приходят с сайта 
            # (не системные и не пользовательские)
            for key, value in new_rec.items():
                if key not in SYSTEM_FIELDS and key not in USER_EDITABLE_FIELDS:
                    old_rec[key] = value
            
            # Сохраняем пользовательские поля из старой записи
            # ВАЖНО: проверяем наличие ключа, а не его значение 
            # (пустая строка - тоже валидное значение, которое мог заполнить пользователь)
            for field in USER_EDITABLE_FIELDS:
                if field in old_rec:
                    # Поле уже существует в старой записи — НЕ перезаписываем
                    # (даже если оно пустое — возможно пользователь его очистил)
                    pass
                else:
                    # Поля нет в старой записи — берем из новой (или ставим пустую строку)
                    old_rec[field] = new_rec.get(field, '')
            
            # Обновляем системные флаги
            old_rec['is_new'] = False
            old_rec['is_expired'] = False
            old_rec['is_mock'] = False
            
            updated_records.append(old_rec)
        
        # 2. Обрабатываем истекшие записи (есть в старом, нет в новом)
        # ВАЖНО: полностью сохраняем старую запись со всеми пользовательскими полями
        for h in expired_hashes:
            old_rec = old_hash_map[h]
            old_rec['is_expired'] = True
            old_rec['is_expiring'] = False
            old_rec['is_new'] = False
            # Пользовательские поля уже есть в old_rec — не трогаем
            updated_records.append(old_rec)
        
        # 3. Обрабатываем новые записи (есть в новом, нет в старом)
        for h in new_only_hashes:
            new_rec = new_hash_map[h]
            new_rec['is_new'] = True
            new_rec['is_expired'] = False
            new_rec['is_mock'] = False
            new_rec['added_at'] = datetime.now().isoformat()
            # Инициализируем пустые пользовательские поля
            for field in USER_EDITABLE_FIELDS:
                if field not in new_rec:
                    new_rec[field] = ''
            updated_records.append(new_rec)
        
        self.records = updated_records
        print(f"✅ Сравнение завершено. Всего записей: {len(self.records)}")
        print(f"   🟢 Новых: {len(new_only_hashes)}")
        print(f"   🔴 Истекших: {len(expired_hashes)}")
        print(f"   📝 Общих (с сохранением пользовательских полей): {len(common_hashes)}")
    
    def _schedule_daily_parser(self):
        """Запланировать ежедневный парсинг в 12:00"""
        async def daily_task():
            while True:
                try:
                    now = datetime.now()
                    next_run = now.replace(hour=12, minute=0, second=0, microsecond=0)
                    if now >= next_run:
                        next_run += timedelta(days=1)
                    
                    wait_seconds = (next_run - now).total_seconds()
                    print(f"⏰ Следующий автоматический парсинг в {next_run.strftime('%H:%M %d.%m.%Y')}")
                    
                    await asyncio.sleep(wait_seconds)
                    
                    print("🔄 Запуск автоматического парсинга...")
                    await self.start_parser({
                        'auto': True,
                        'days_back': None,  # Все данные
                        'headless': True
                    })
                    
                except Exception as e:
                    print(f"⚠️ Ошибка в ежедневном парсинге: {e}")
                    await asyncio.sleep(3600)  # Ждем час и пробуем снова
        
        self._daily_task = daily_task
        
        # Пытаемся запустить, если есть event loop
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(daily_task())
            self._daily_task_started = True
        except RuntimeError:
            print("⏳ Ежедневный парсинг будет запущен при старте API сервера")
    
    def start_daily_parser(self):
        """Запустить ежедневный парсинг (вызывается при старте API)"""
        if self._daily_task and not self._daily_task_started:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._daily_task())
                self._daily_task_started = True
                print("✅ Ежедневный парсинг запущен")
            except RuntimeError:
                print("⚠️ Нет running loop для запуска ежедневного парсинга")
    
    def get_status(self):
        """Получить статус парсера"""
        return {
            "status": self.status,
            "progress": self.progress,
            "total_records": len(self.records),
            "current_record": self.current_record,
            "message": self.message,
            "is_running": self.is_running,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_records(self, limit: int = 100, offset: int = 0, include_new_only: bool = False) -> List[Dict]:
        """Получить записи с пагинацией"""
        records = self.records
        
        if include_new_only:
            records = [r for r in records if r.get('is_new', False)]
        
        return records[offset:offset + limit]
    
    def get_records_count(self) -> int:
        """Получить общее количество записей"""
        return len(self.records)
    
    def get_new_records_count(self) -> int:
        """Получить количество новых записей"""
        return len([r for r in self.records if r.get('is_new', False)])
    
    def get_expiring_records_count(self) -> int:
        """Получить количество истекающих записей"""
        return len([r for r in self.records if r.get('is_expiring', False)])
    
    def get_expired_records_count(self) -> int:
        """Получить количество истекших записей"""
        return len([r for r in self.records if r.get('is_expired', False)])
    
    async def start_parser(self, config: Optional[Dict] = None):
        """Запустить парсер"""
        if self.is_running:
            raise Exception("Парсер уже запущен")
        
        self.status = "running"
        self.progress = 0
        self.total_records = 0
        self.current_record = 0
        self.message = "Инициализация..."
        self.is_running = True
        self.should_stop = False
        self.started_at = datetime.now()
        self.completed_at = None
        
        # Запускаем в фоне
        asyncio.create_task(self._run_parser(config))
        
        return {
            "message": "Парсер запущен",
            "status": "running"
        }
        
    async def _run_parser(self, config: Optional[Dict] = None):
        """
        Запуск парсера.
        ПОКА РАБОТАЕТ В РЕЖИМЕ ИМИТАЦИИ С СРАВНЕНИЕМ.
        Когда появится реальный парсинг - раскомментировать реальный код.
        """
        try:
            # ============================================================
            # ИМИТАЦИЯ РЕАЛЬНОГО ПАРСИНГА (для тестирования)
            # Когда заработает реальный парсинг - закомментировать этот блок
            # ============================================================
            # await self._mock_parse_with_comparison(config)
            # return
            # ============================================================
            
            # ============================================================
            # РЕАЛЬНЫЙ ПАРСИНГ (закомментирован до готовности)
            # Раскомментировать когда появится возможность реального парсинга
            # ============================================================
            
            import sys
            import os
            import platform
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # ✅ Кросс-платформенный импорт
            if platform.system() == "Linux":
                from main_linux import main_linux_with_progress as main_parser_with_progress
            else:
                from main_windows import main_windows_with_progress as main_parser_with_progress
            
            self.progress = 0
            self.message = "Инициализация..."
            await self._update_status()
            await asyncio.sleep(0.3)
            
            self.progress = 10
            self.message = "Запуск браузера..."
            await self._update_status()
            await asyncio.sleep(0.3)
            
            self.progress = 20
            self.message = "Открытие сайта..."
            await self._update_status()
            await asyncio.sleep(0.3)
            
            self.progress = 30
            self.message = "Авторизация..."
            await self._update_status()
            await asyncio.sleep(0.3)
            
            self.progress = 40
            self.message = "Вход в систему..."
            await self._update_status()
            await asyncio.sleep(0.3)
            
            self.progress = 50
            self.message = "Сбор данных..."
            await self._update_status()
            
            old_records = list(self.records)
            
            new_records = await main_parser_with_progress(
                progress_callback=self._update_progress,
                stop_callback=lambda: self.should_stop,
                config=config
            )
            
            if self.should_stop:
                self.status = "stopped"
                self.message = "Остановлен пользователем"
                self.is_running = False
                await self._update_status()
                return
            
            self.progress = 80
            self.message = "Сравнение данных..."
            await self._update_status()
            self._compare_and_update_records(old_records, new_records)
            
            self.progress = 90
            self.message = "Обновление флагов..."
            await self._update_status()
            self._update_record_flags()
            self._save_records()
            
            self.progress = 95
            self.message = "Экспорт в Excel..."
            await self._update_status()
            self._export_to_fixed_excel()
            
            new_count = self.get_new_records_count()
            expiring_count = self.get_expiring_records_count()
            expired_count = self.get_expired_records_count()
            
            self.status = "completed"
            self.progress = 100
            self.message = f"✅ Парсинг завершен! Новых: {new_count}, истекающих: {expiring_count}, истекших: {expired_count}"
            self.completed_at = datetime.now()
            self.is_running = False
            
            await self._update_status()
            
        except Exception as e:
            self.status = "error"
            self.message = f"❌ Ошибка: {str(e)}"
            self.is_running = False
            await self._update_status()
    
    # async def _run_parser(self, config: Optional[Dict] = None):
    #     """
    #     Запуск парсера.
    #     ПОКА РАБОТАЕТ В РЕЖИМЕ ИМИТАЦИИ С СРАВНЕНИЕМ.
    #     Когда появится реальный парсинг - раскомментировать реальный код.
    #     """
    #     try:
    #         # ============================================================
    #         # ИМИТАЦИЯ РЕАЛЬНОГО ПАРСИНГА (для тестирования)
    #         # Когда заработает реальный парсинг - закомментировать этот блок
    #         # ============================================================
    #         # await self._mock_parse_with_comparison(config)
    #         # return
    #         # ============================================================
            
    #         # ============================================================
    #         # РЕАЛЬНЫЙ ПАРСИНГ (закомментирован до готовности)
    #         # Раскомментировать когда появится возможность реального парсинга
    #         # ============================================================
            
    #         import sys
    #         import os
    #         sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
    #         from main_windows import main_windows_with_progress
            
    #         # Этапы прогресса
    #         self.progress = 0
    #         self.message = "Инициализация..."
    #         await self._update_status()
    #         await asyncio.sleep(0.3)
            
    #         self.progress = 10
    #         self.message = "Запуск браузера..."
    #         await self._update_status()
    #         await asyncio.sleep(0.3)
            
    #         self.progress = 20
    #         self.message = "Открытие сайта..."
    #         await self._update_status()
    #         await asyncio.sleep(0.3)
            
    #         self.progress = 30
    #         self.message = "Авторизация..."
    #         await self._update_status()
    #         await asyncio.sleep(0.3)
            
    #         self.progress = 40
    #         self.message = "Вход в систему..."
    #         await self._update_status()
    #         await asyncio.sleep(0.3)
            
    #         self.progress = 50
    #         self.message = "Сбор данных..."
    #         await self._update_status()
            
    #         # Сохраняем старые записи для сравнения
    #         old_records = list(self.records)
            
    #         # Запускаем реальный парсер
    #         new_records = await main_windows_with_progress(
    #             progress_callback=self._update_progress,
    #             stop_callback=lambda: self.should_stop,
    #             config=config
    #         )
            
    #         if self.should_stop:
    #             self.status = "stopped"
    #             self.message = "Остановлен пользователем"
    #             self.is_running = False
    #             await self._update_status()
    #             return
            
    #         self.progress = 80
    #         self.message = "Сравнение данных..."
    #         await self._update_status()
            
    #         # Сравниваем старые и новые записи
    #         self._compare_and_update_records(old_records, new_records)
            
    #         self.progress = 90
    #         self.message = "Обновление флагов..."
    #         await self._update_status()
            
    #         # Обновляем флаги истечения
    #         self._update_record_flags()
            
    #         # Сохраняем записи
    #         self._save_records()
            
    #         self.progress = 95
    #         self.message = "Экспорт в Excel..."
    #         await self._update_status()
            
    #         # Экспортируем в Excel
    #         self._export_to_fixed_excel()
            
    #         new_count = self.get_new_records_count()
    #         expiring_count = self.get_expiring_records_count()
    #         expired_count = self.get_expired_records_count()
            
    #         self.status = "completed"
    #         self.progress = 100
    #         self.message = f"✅ Парсинг завершен! Новых: {new_count}, истекающих: {expiring_count}, истекших: {expired_count}"
    #         self.completed_at = datetime.now()
    #         self.is_running = False
            
    #         await self._update_status()
            
            
    #     except Exception as e:
    #         self.status = "error"
    #         self.message = f"❌ Ошибка: {str(e)}"
    #         self.is_running = False
    #         await self._update_status()
    
    async def _generate_mock_site_data(self, old_records: List[Dict]) -> List[Dict]:
        """
        Создаёт «новый» набор записей, который как будто пришёл с сайта.
        
        Логика имитации реального поведения сайта:
        - Записи с истекшим сроком (date_to < сегодня) удаляются с сайта
        - Записи с действующим сроком остаются на сайте
        - Добавляются новые случайные записи
        
        ВАЖНО: существующие записи сохраняют те же ключевые поля 
        (fio, serial_number, date_from, date_to), чтобы хеш НЕ менялся.
        """
        new_set = []
        today = datetime.now()
        
        if old_records:
            for rec in old_records:
                # Проверяем, истек ли срок действия
                is_expired = False
                if rec.get('date_to'):
                    try:
                        date_to_str = rec['date_to']
                        if ', ' in date_to_str:
                            date_to_str = date_to_str.split(', ')[0]
                        date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                        if date_to < today.date():
                            is_expired = True
                    except:
                        pass
                
                # Если срок НЕ истек — запись остаётся на сайте
                if not is_expired:
                    rec_copy = rec.copy()
                    
                    # Убираем служебные флаги (они будут проставлены при сравнении)
                    for flag in ['is_new', 'is_expired', 'is_expiring', 'days_left', 'is_mock']:
                        rec_copy.pop(flag, None)
                    
                    new_set.append(rec_copy)
                # Если срок истек — запись НЕ попадает в новый набор
                # (казначейство удалило её с сайта)
        
        # Добавляем случайные новые записи (от 1 до 5)
        new_random_count = random.randint(1, 5)
        new_random_records = await self._generate_test_data_entries(new_random_count)
        
        for rec in new_random_records:
            # Убираем служебные флаги
            for flag in ['is_new', 'is_expired', 'is_expiring', 'days_left', 'is_mock']:
                rec.pop(flag, None)
            new_set.append(rec)
        
        # Логируем статистику
        old_count = len(old_records)
        kept_count = len(new_set) - new_random_count
        removed_count = old_count - kept_count
        
        print(f"🌐 Имитация сайта:")
        print(f"   📋 Было на сайте: {old_count}")
        print(f"   ✅ Осталось (срок не истек): {kept_count}")
        print(f"   🗑️ Удалено (срок истек): {removed_count}")
        print(f"   🆕 Новых сертификатов: {new_random_count}")
        
        return new_set
    
    async def _mock_parse_with_comparison(self, config: Optional[Dict] = None):
        """
        Имитация реального парсинга с полным циклом сравнения.
        
        Логика:
        1. Сохраняем старый список (old_records)
        2. Генерируем новый набор (имитация сайта)
        3. Сравниваем:
        - Записи, которые были в старом но исчезли → is_expired=True (красные)
        - Записи, которые появились только в новом → is_new=True (зеленые/берёзовые)
        - Записи, которые есть в обоих → обновляем неключевые поля, 
            сбрасываем is_new и is_expired
        4. Обновляем флаги истечения (is_expiring, days_left)
        5. Сохраняем и экспортируем
        """
        try:
            self.message = "🔄 Имитация реального парсинга..."
            self.progress = 5
            await self._update_status()
            await asyncio.sleep(0.3)
            
            # 1. Сохраняем старый список для сравнения
            old_records = list(self.records)  # глубокая копия текущих записей
            self.message = f"📋 Сохранено {len(old_records)} старых записей для сравнения"
            self.progress = 10
            await self._update_status()
            await asyncio.sleep(0.5)
            
            # 2. Генерируем новый список записей (имитация того, что пришло с сайта)
            self.message = "🌐 Имитация получения данных с сайта..."
            self.progress = 15
            await self._update_status()
            
            new_records = await self._generate_mock_site_data(old_records)
            
            total_new = len(new_records)
            self.message = f"📥 Получено {total_new} записей с 'сайта'"
            self.progress = 30
            await self._update_status()
            await asyncio.sleep(0.5)
            
            # 3. Сравниваем старые и новые записи
            self.message = "🔄 Сравнение старых и новых записей..."
            self.progress = 40
            await self._update_status()
            
            self._compare_and_update_records(old_records, new_records)
            
            self.progress = 60
            await self._update_status()
            await asyncio.sleep(0.3)
            
            # 4. Обновляем временные флаги (is_expiring, days_left)
            self.message = "📅 Обновление сроков действия..."
            self.progress = 70
            await self._update_status()
            
            self._update_record_flags()
            
            self.progress = 80
            await self._update_status()
            await asyncio.sleep(0.3)
            
            # 5. Сохраняем JSON
            self.message = "💾 Сохранение данных..."
            self.progress = 85
            await self._update_status()
            
            self._save_records()
            
            # 6. Экспортируем в Excel
            self.message = "📊 Экспорт в Excel..."
            self.progress = 90
            await self._update_status()
            
            self._export_to_fixed_excel()
            
            # 7. Финальная статистика
            new_count = self.get_new_records_count()
            expiring_count = self.get_expiring_records_count()
            expired_count = self.get_expired_records_count()
            
            self.status = "completed"
            self.progress = 100
            self.message = (
                f"✅ Имитация парсинга завершена! "
                f"🟢 Новых: {new_count}, "
                f"🟠 Истекающих: {expiring_count}, "
                f"🔴 Истекших: {expired_count}"
            )
            self.completed_at = datetime.now()
            self.is_running = False
            
            await self._update_status()
            
        except Exception as e:
            self.status = "error"
            self.message = f"❌ Ошибка имитации: {str(e)}"
            self.is_running = False
            await self._update_status()
    
    async def _generate_test_data_entries(self, count: int) -> List[Dict]:
        """
        Генерация указанного количества тестовых записей.
        
        Реалистичные сроки:
        - Сертификат действует примерно 1.5 года (540 дней)
        - date_from: 1-540 дней назад
        - date_to: date_from + 540 дней
        
        Часть записей генерируется с истекающим сроком (≤15 дней до конца).
        """
        test_records = []
        
        names = [
            "Иванов Иван Иванович",
            "Петров Петр Петрович",
            "Сидоров Сидор Сидорович",
            "Козлова Екатерина Дмитриевна",
            "Смирнов Алексей Владимирович",
            "Кузнецова Ольга Сергеевна",
            "Попов Дмитрий Николаевич",
            "Соколова Анна Михайловна",
            "Михайлов Сергей Александрович",
            "Федорова Татьяна Петровна",
            "Топорова Лариса Анатольевна",
            "Маер Дмитрий Александрович",
            "Новиков Андрей Сергеевич",
            "Морозова Елена Викторовна",
            "Волков Павел Дмитриевич"
        ]
        
        serial_prefixes = ["00", "01", "02", "03", "04"]
        serial_suffixes = ["ABCDEF", "123456", "XYZ789", "QWE456", "RTY789"]
        today = datetime.now()
        
        # Сертификат действует ~1.5 года
        cert_validity_days = 540
        
        for i in range(count):
            # Определяем тип записи
            rand_val = random.random()
            
            if rand_val < 0.25:
                # 25% — истекающие (осталось 1-15 дней)
                days_left = random.randint(1, 15)
                date_to = today + timedelta(days=days_left)
                date_from = date_to - timedelta(days=cert_validity_days)
            elif rand_val < 0.45:
                # 20% — только что истекшие (просрочены на 1-30 дней)
                days_overdue = random.randint(1, 30)
                date_to = today - timedelta(days=days_overdue)
                date_from = date_to - timedelta(days=cert_validity_days)
            elif rand_val < 0.65:
                # 20% — давно истекшие (просрочены на 31-365 дней)
                days_overdue = random.randint(31, 365)
                date_to = today - timedelta(days=days_overdue)
                date_from = date_to - timedelta(days=cert_validity_days)
            else:
                # 35% — нормальные (осталось 16-540 дней)
                days_left = random.randint(16, cert_validity_days)
                date_to = today + timedelta(days=days_left)
                date_from = date_to - timedelta(days=cert_validity_days)
            
            date_from_str = date_from.strftime("%d.%m.%Y, %H:%M")
            date_to_str = date_to.strftime("%d.%m.%Y, %H:%M")
            
            serial = (
                f"{random.choice(serial_prefixes)}"
                f"{random.randint(10000000, 99999999):08d}"
                f"{random.choice(serial_suffixes)}"
            )
            
            record = {
                "date_from": date_from_str,
                "fio": random.choice(names),
                "serial_number": serial,
                "date_to": date_to_str,
                "key_type": random.choice(["ЭЦП", "СКЗИ", "КриптоПро"]),
                "key_carrier_number": "",        # Пользовательское поле
                "destruction_date": "",          # Пользовательское поле
                "destruction_signature": "",     # Пользовательское поле
                "notes": "",                     # Пользовательское поле
                "is_new": False,
                "is_expiring": False,
                "is_expired": False,
                "is_mock": False
            }
            test_records.append(record)
        
        return test_records
    
    async def _generate_test_data(self, days_back: int = 15) -> List[Dict]:
        """Генерация тестовых данных за указанный период (для обратной совместимости)"""
        count = random.randint(5, 15)
        return await self._generate_test_data_entries(count)
    
    def _import_user_fields_from_excel(self, filepath: str) -> int:
        """
        Импорт пользовательских полей из Excel файла.
        
        Сопоставляет записи по ключевым полям:
        - E: ФИО пользователя (fio)
        - H: Серийный номер (serial_number)
        
        Импортирует поля:
        - I: Номер разового ключевого носителя (key_carrier_number)
        - J: Отметка об уничтожении - Дата (destruction_date)
        - K: Отметка об уничтожении - Подпись (destruction_signature)
        - L: Примечание (notes)
        
        Returns:
            int: Количество обновленных записей
        """
        import openpyxl
        
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            
            # Находим лист "СКЗИ"
            if 'СКЗИ' in wb.sheetnames:
                ws = wb['СКЗИ']
            else:
                ws = wb.active
            
            updated_count = 0
            
            # Пропускаем заголовок (строка 1)
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or len(row) < 8:
                    continue
                
                # Ключевые поля для сопоставления
                fio = str(row[4]).strip() if row[4] else ''          # E: ФИО
                serial_number = str(row[7]).strip() if row[7] else '' # H: Серийный номер
                
                if not fio or not serial_number:
                    continue
                
                # Пользовательские поля
                key_carrier_number = str(row[8]).strip() if len(row) > 8 and row[8] else ''      # I
                destruction_date = str(row[9]).strip() if len(row) > 9 and row[9] else ''        # J
                destruction_signature = str(row[10]).strip() if len(row) > 10 and row[10] else '' # K
                notes = str(row[11]).strip() if len(row) > 11 and row[11] else ''                # L
                
                # Пропускаем если все пользовательские поля пустые
                if not any([key_carrier_number, destruction_date, destruction_signature, notes]):
                    continue
                
                # Ищем запись в сервисе по ключевым полям
                for record in self.records:
                    rec_fio = record.get('fio', '').strip()
                    rec_serial = record.get('serial_number', '').strip()
                    
                    if rec_fio == fio and rec_serial == serial_number:
                        # Обновляем только если поле не пустое в Excel
                        if key_carrier_number:
                            record['key_carrier_number'] = key_carrier_number
                        if destruction_date:
                            record['destruction_date'] = destruction_date
                        if destruction_signature:
                            record['destruction_signature'] = destruction_signature
                        if notes:
                            record['notes'] = notes
                        
                        updated_count += 1
                        break
            
            wb.close()
            return updated_count
            
        except Exception as e:
            print(f"⚠️ Ошибка импорта пользовательских полей из Excel: {e}")
            return 0
        
    def _export_to_fixed_excel(self):
        """
        Экспорт в backend/output/Журнал_СКЗИ.xlsx и backend/output/Журнал_СКЗИ.json
        Возвращает dict с результатом {'file_locked': True/False}
        """
        try:
            from ...export.excel_exporter import ExcelExporter, is_file_locked
            from ...core.config import AppConfig
            
            app_config = AppConfig()
            exporter = ExcelExporter(
                app_config.export,
                app_config.skzi_type,
                app_config.service_type,
                app_config.key_type
            )
            
            current_file = os.path.abspath(__file__)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
            
            output_dir = os.path.join(backend_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            excel_path = os.path.join(output_dir, 'Журнал_СКЗИ.xlsx')
            json_path = os.path.join(output_dir, 'Журнал_СКЗИ.json')
            
            # Проверяем, открыт ли файл
            if os.path.exists(excel_path) and is_file_locked(excel_path):
                print(f"⛔ Файл {os.path.basename(excel_path)} открыт в Excel!")
                print(f"   💡 Закройте файл и нажмите 'Экспорт' ещё раз")
                return {'file_locked': True}
            
            # Импорт полей из Excel (если файл доступен)
            if os.path.exists(excel_path):
                print("📥 Импорт пользовательских полей...")
                imported_count = self._import_user_fields_from_excel(excel_path)
                if imported_count > 0:
                    print(f"   ✅ Импортировано полей из {imported_count} записей")
                    self._save_records()
            
            # Экспорт в Excel
            result = exporter.export_to_excel(
                records=self.records,
                output_path=excel_path,
                highlight_new=True,
                highlight_expiring=True,
                highlight_expired=True
            )
            
            if result.get('output'):
                print(f"📊 Excel обновлён: {result['output']}")
                self.last_files['excel'] = result['output']
            
            if result.get('download'):
                print(f"📥 Копия в Downloads: {result['download']}")
                # Открываем папку Downloads
                if os.name == 'nt':
                    download_dir = os.path.dirname(result['download'])
                    os.startfile(download_dir)
                    print(f"📂 Папка Downloads открыта")
            
            # Сохраняем JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'records': self.records,
                    'last_updated': datetime.now().isoformat(),
                    'total_count': len(self.records)
                }, f, ensure_ascii=False, indent=2)
            print(f"📄 JSON сохранён: {json_path}")
            
            return {'file_locked': False}
            
        except Exception as e:
            print(f"⚠️ Ошибка экспорта: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def stop_parser(self, force: bool = False):
        """Остановить парсер"""
        if not self.is_running:
            raise Exception("Парсер не запущен")
        
        self.should_stop = True
        
        if force:
            self.status = "stopped"
            self.is_running = False
            self.message = "Принудительно остановлен"
            await self._update_status()
        
        return {"message": "Парсер останавливается..."}
    
    async def _update_progress(self, current: int, total: int, message: str = None):
        """Обновление прогресса (для колбэков реального парсера)"""
        if total > 0:
            self.progress = 50 + (current / total) * 40  # 50-90%
        self.current_record = current
        self.total_records = total
        if message:
            self.message = message
        await self._update_status()
    
    async def _update_status(self):
        """Обновление статуса для всех подписчиков (WebSocket)"""
        status = self.get_status()
        
        # Добавляем записи (последние 1000)
        if self.records:
            status['records'] = self.records[-1000:] if len(self.records) > 1000 else self.records
        else:
            status['records'] = []
        
        # Удаляем мертвые подписки
        to_remove = []
        for subscriber in self.subscribers:
            try:
                await subscriber.send_json(status)
            except:
                to_remove.append(subscriber)
        
        for subscriber in to_remove:
            if subscriber in self.subscribers:
                self.subscribers.remove(subscriber)
    
    def add_subscriber(self, subscriber):
        """Добавить подписчика (WebSocket)"""
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)
    
    def remove_subscriber(self, subscriber):
        """Удалить подписчика"""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
            
    async def notify_subscribers(self, message: dict):
        """Отправить сообщение всем WebSocket подписчикам"""
        disconnected = []
        for ws in self.subscribers:
            try:
                await ws.send_json(message)
            except Exception as e:
                print(f"⚠️ Ошибка отправки подписчику: {e}")
                disconnected.append(ws)
        
        # Удаляем отключенных
        for ws in disconnected:
            if ws in self.subscribers:
                self.subscribers.remove(ws)
    
    def export_records(self, format: str = "excel") -> Dict:
        """Экспорт записей в указанном формате"""
        try:
            if format == "excel":
                # Вызываем экспорт
                result = self._export_to_fixed_excel()
                
                # ✅ Если экспорт не удался из-за блокировки
                if result and result.get('file_locked'):
                    return {
                        "filepath": None,
                        "format": "excel",
                        "count": len(self.records),
                        "file_locked": True,
                        "message": "Файл открыт в Excel. Закройте файл и повторите экспорт.",
                        "new_count": self.get_new_records_count(),
                        "expiring_count": self.get_expiring_records_count(),
                        "expired_count": self.get_expired_records_count()
                    }
                
                return {
                    "filepath": self.last_files.get('excel', ''),
                    "format": "excel",
                    "count": len(self.records),
                    "new_count": self.get_new_records_count(),
                    "expiring_count": self.get_expiring_records_count(),
                    "expired_count": self.get_expired_records_count()
                }
            
            elif format == "json":
                return {
                    "data": self.records,
                    "format": "json",
                    "count": len(self.records),
                    "new_count": self.get_new_records_count(),
                    "expiring_count": self.get_expiring_records_count(),
                    "expired_count": self.get_expired_records_count()
                }
            
            elif format == "csv":
                return {
                    "data": self.records,
                    "format": "csv",
                    "count": len(self.records),
                    "new_count": self.get_new_records_count(),
                    "expiring_count": self.get_expiring_records_count(),
                    "expired_count": self.get_expired_records_count()
                }
            
            else:
                raise Exception(f"Неподдерживаемый формат: {format}")
                
        except Exception as e:
            raise Exception(f"Ошибка экспорта: {str(e)}")
                
    # def export_records(self, format: str = "excel") -> Dict:
    #     """Экспорт записей в указанном формате"""
    #     try:
    #         if format == "excel":
    #             self._export_to_fixed_excel()
    #             return {
    #                 "filepath": self.last_files.get('excel', ''),
    #                 "format": "excel",
    #                 "count": len(self.records),
    #                 "new_count": self.get_new_records_count(),
    #                 "expiring_count": self.get_expiring_records_count(),
    #                 "expired_count": self.get_expired_records_count()
    #             }
            
    #         elif format == "json":
    #             return {
    #                 "data": self.records,
    #                 "format": "json",
    #                 "count": len(self.records),
    #                 "new_count": self.get_new_records_count(),
    #                 "expiring_count": self.get_expiring_records_count(),
    #                 "expired_count": self.get_expired_records_count()
    #             }
            
    #         elif format == "csv":
    #             # ✅ Отдаём сырые данные, фронт сам сгенерирует CSV с BOM
    #             return {
    #                 "data": self.records,
    #                 "format": "csv",
    #                 "count": len(self.records),
    #                 "new_count": self.get_new_records_count(),
    #                 "expiring_count": self.get_expiring_records_count(),
    #                 "expired_count": self.get_expired_records_count()
    #             }
            
    #         else:
    #             raise Exception(f"Неподдерживаемый формат: {format}")
                
    #     except Exception as e:
    #         raise Exception(f"Ошибка экспорта: {str(e)}")
    
    def clear_new_flag(self):
        """Очистить флаг новых записей (после просмотра пользователем)"""
        count = 0
        for record in self.records:
            if record.get('is_new'):
                record['is_new'] = False
                count += 1
        self._save_records()
        return {"message": f"Флаг 'новый' очищен у {count} записей"}
    
    def reschedule_daily_parser(self, time_str: str):
        """Перезапустить ежедневный парсинг с новым временем"""
        try:
            # Парсим время
            hours, minutes = map(int, time_str.split(':'))
            
            # Останавливаем текущую задачу
            self._daily_task_stop = True
            
            # Создаем новую задачу с новым временем
            async def daily_task():
                while True:
                    if hasattr(self, '_daily_task_stop') and self._daily_task_stop:
                        break
                    try:
                        now = datetime.now()
                        next_run = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                        if now >= next_run:
                            next_run += timedelta(days=1)
                        
                        wait_seconds = (next_run - now).total_seconds()
                        print(f"⏰ Следующий автоматический парсинг в {next_run.strftime('%H:%M %d.%m.%Y')}")
                        
                        await asyncio.sleep(wait_seconds)
                        
                        if hasattr(self, '_daily_task_stop') and self._daily_task_stop:
                            break
                        
                        print("🔄 Запуск автоматического парсинга...")
                        await self.start_parser({
                            'auto': True,
                            'days_back': None,
                            'headless': True
                        })
                        
                    except Exception as e:
                        print(f"⚠️ Ошибка в ежедневном парсинге: {e}")
                        await asyncio.sleep(3600)
            
            # Запускаем новую задачу
            self._daily_task_stop = False
            self._daily_task = daily_task
            
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(daily_task())
                self._daily_task_started = True
            except RuntimeError:
                pass
            
            print(f"✅ Ежедневный парсинг перепланирован на {time_str}")
            return {"message": f"Ежедневный парсинг перепланирован на {time_str}"}
            
        except Exception as e:
            print(f"⚠️ Ошибка перепланирования: {e}")
            raise Exception(f"Ошибка перепланирования: {str(e)}")


# Создаем глобальный экземпляр сервиса
parser_service = ParserService()