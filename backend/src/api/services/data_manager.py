"""
Управление данными: загрузка, сохранение, сравнение записей
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

from ...utils.logger import get_logger

logger = get_logger(__name__)


class DataManager:
    """Управление данными"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.records_file = os.path.join(data_dir, "records.json")
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Создать директорию для данных если её нет"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_records(self) -> List[Dict]:
        """Загрузить записи из файла"""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = data.get('records', [])
                    logger.info(f"📂 Загружено {len(records)} записей")
                    return records
            except Exception as e:
                logger.error(f"⚠️ Ошибка загрузки данных: {e}")
                return []
        return []
    
    def save_records(self, records: List[Dict]) -> bool:
        """Сохранить записи в файл"""
        try:
            data = {
                'records': records,
                'last_updated': datetime.now().isoformat(),
                'total_count': len(records)
            }
            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Сохранено {len(records)} записей")
            return True
        except Exception as e:
            logger.error(f"⚠️ Ошибка сохранения данных: {e}")
            return False
    
    def merge_records(self, new_records: List[Dict]) -> List[Dict]:
        """
        Объединить новые записи с существующими:
        - Новые записи -> добавляются с флагом is_new=True (зеленый)
        - Исчезнувшие записи -> помечаются is_expired=True (красный)
        - Существующие записи -> обновляются
        """
        # Загружаем существующие записи
        existing_records = self.load_records()
        
        if not existing_records:
            # Если нет старых записей, все новые помечаем как новые
            for record in new_records:
                record['is_new'] = True
                record['is_expired'] = False
                record['is_expiring'] = False
            return new_records
        
        # Создаем словарь существующих записей по уникальному ключу
        existing_map = {}
        for record in existing_records:
            key = self._get_record_key(record)
            existing_map[key] = record
        
        # Множество ключей новых записей
        new_keys = set()
        merged_records = []
        
        # Обрабатываем новые записи
        for record in new_records:
            key = self._get_record_key(record)
            new_keys.add(key)
            
            if key in existing_map:
                # Запись уже существует - обновляем данные
                existing = existing_map[key]
                # Сохраняем флаги is_new и is_expired
                was_new = existing.get('is_new', False)
                was_expired = existing.get('is_expired', False)
                
                # Обновляем запись новыми данными
                for k, v in record.items():
                    existing[k] = v
                
                # Сохраняем флаги
                if was_new:
                    existing['is_new'] = True
                if was_expired:
                    existing['is_expired'] = True
                
                # Обновляем флаги истечения
                self._update_expiration_flags(existing)
                
                merged_records.append(existing)
            else:
                # Новая запись
                record['is_new'] = True
                record['is_expired'] = False
                self._update_expiration_flags(record)
                merged_records.append(record)
        
        # Обрабатываем записи, которые исчезли из нового JSON
        for key, record in existing_map.items():
            if key not in new_keys:
                # Запись исчезла - помечаем как истекшую
                record['is_expired'] = True
                record['is_new'] = False
                record['is_expiring'] = False
                # Сохраняем дату истечения
                if not record.get('expired_at'):
                    record['expired_at'] = datetime.now().isoformat()
                merged_records.append(record)
        
        return merged_records
    
    def _get_record_key(self, record: Dict) -> str:
        """Получить уникальный ключ записи (по серийному номеру)"""
        serial = record.get('serial_number', '')
        fio = record.get('fio', '')
        return f"{serial}:{fio}".strip()
    
    def _update_expiration_flags(self, record: Dict):
        """Обновить флаги истечения записи"""
        today = datetime.now().date()
        
        if record.get('date_to'):
            try:
                date_to_str = record['date_to']
                if ', ' in date_to_str:
                    date_to_str = date_to_str.split(', ')[0]
                date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                days_left = (date_to - today).days
                
                record['days_left'] = days_left
                
                if days_left < 0:
                    record['is_expired'] = True
                    record['is_expiring'] = False
                elif 0 <= days_left <= 15:
                    record['is_expiring'] = True
                    record['is_expired'] = False
                else:
                    record['is_expiring'] = False
                    record['is_expired'] = False
            except Exception as e:
                logger.warning(f"Ошибка парсинга даты: {e}")
                record['is_expiring'] = False
                record['is_expired'] = False
                record['days_left'] = None