import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

class ExcelHandler:
    """Обработчик Excel файлов"""
    
    def __init__(self, data_manager=None):
        self.data_manager = data_manager
        
    def read_excel(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Прочитать Excel и конвертировать в JSON структуру"""
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                print(f"❌ Файл не найден: {file_path}")
                return None
            
            # Читаем все листы
            excel_data = pd.read_excel(file_path, sheet_name=None)
            records = []
            
            for sheet_name, df in excel_data.items():
                df = df.fillna('')
                records.extend(self._process_sheet(df, sheet_name))
            
            result = {
                'records': records,
                'total': len(records),
                'updated_at': datetime.now().isoformat(),
                'source_file': os.path.basename(file_path),
                'sheets': list(excel_data.keys())
            }
            
            # Если есть data_manager, обновляем через него
            if self.data_manager:
                self.data_manager.update_records(records)
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка чтения Excel: {e}")
            return None
    
    def _process_sheet(self, df: pd.DataFrame, sheet_name: str) -> List[Dict]:
        """Обработать один лист Excel"""
        from .status_calculator import StatusCalculator
        
        records = []
        
        # Маппинг колонок (русские -> английские)
        column_mapping = {
            'ФИО': 'fio',
            'fio': 'fio',
            'ФИО пользователя': 'fio',
            'Серийный номер': 'serial_number',
            'serial_number': 'serial_number',
            'Дата установки': 'date_from',
            'date_from': 'date_from',
            'Срок действия': 'date_to',
            'date_to': 'date_to',
            'Тип ключа': 'key_type',
            'key_type': 'key_type',
            '№ носителя': 'key_carrier_number',
            'key_carrier_number': 'key_carrier_number',
            '№ ключевого носителя': 'key_carrier_number',
            'Тип СКЗИ': 'skzi_type',
            'skzi_type': 'skzi_type',
            'Обслуживание': 'service_type',
            'service_type': 'service_type',
            'Уничтожение (дата)': 'destruction_date',
            'destruction_date': 'destruction_date',
            'Дата уничтожения': 'destruction_date',
            'Уничтожение (подпись)': 'destruction_signature',
            'destruction_signature': 'destruction_signature',
            'Подпись': 'destruction_signature',
            'Примечание': 'notes',
            'notes': 'notes'
        }
        
        # Переименовываем колонки если нужно
        df = df.rename(columns=column_mapping)
        
        for idx, row in df.iterrows():
            record = {
                'id': idx + 1,
                'fio': str(row.get('fio', '')),
                'serial_number': str(row.get('serial_number', '')),
                'date_from': str(row.get('date_from', '')),
                'date_to': str(row.get('date_to', '')),
                'key_type': str(row.get('key_type', 'ЭЦП')),
                'key_carrier_number': str(row.get('key_carrier_number', '')),
                '_type': str(row.get('skzi_type', 'КриптоПро CSP 5.0')),
                'service_type': str(row.get('service_type', 'Установка ключевых документов')),
                'destruction_date': str(row.get('destruction_date', '')),
                'destruction_signature': str(row.get('destruction_signature', '')),
                'notes': str(row.get('notes', '')),
                'sheet': sheet_name,
                'row': idx + 2  # +2 потому что 1 строка - заголовки
            }
            
            # Вычисляем статус
            status = StatusCalculator.calculate(record)
            record.update(status)
            
            records.append(record)
        
        return records
    
    def save_json(self, data: Dict[str, Any], output_path: str) -> bool:
        """Сохранить данные в JSON"""
        try:
            import json
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON сохранен: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")
            return False