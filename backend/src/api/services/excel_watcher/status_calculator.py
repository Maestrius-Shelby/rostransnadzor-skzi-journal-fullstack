from datetime import datetime
from typing import Dict, Any

class StatusCalculator:
    """Расчет статусов записей на основе дат"""
    
    @staticmethod
    def calculate(record: Dict[str, Any]) -> Dict[str, Any]:
        """Вычислить статус записи"""
        status = {
            'is_new': False,
            'is_expired': False,
            'is_expiring': False,
            'is_mock': False,
            'days_left': None
        }
        
        try:
            date_to_str = record.get('date_to', '')
            if date_to_str and date_to_str not in ['None', '', '—']:
                date_to = StatusCalculator._parse_date(date_to_str)
                
                if date_to:
                    now = datetime.now()
                    days_left = (date_to - now).days
                    status['days_left'] = days_left
                    
                    if days_left < 0:
                        status['is_expired'] = True
                    elif days_left <= 30:
                        status['is_expiring'] = True
                    else:
                        status['is_new'] = True
            else:
                status['is_new'] = True
                
        except Exception as e:
            print(f"⚠️ Ошибка расчета статуса: {e}")
            
        return status
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Парсинг даты из разных форматов"""
        formats = [
            '%d.%m.%Y, %H:%M',
            '%d.%m.%Y',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y',
            '%d/%m/%Y %H:%M'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None