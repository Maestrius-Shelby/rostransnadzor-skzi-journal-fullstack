"""
Управление скроллом и сбором данных
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

from ..utils.logger import get_logger
from ..core.browser_manager import BrowserManager
from ..core.config import ParsingConfig
from .data_parser import DataParser

logger = get_logger(__name__)


class ScrollManager:
    """Управление скроллом и сбором данных"""
    
    def __init__(
        self,
        browser: BrowserManager,
        parser: DataParser,
        config: ParsingConfig
    ):
        self.browser = browser
        self.parser = parser
        self.config = config
        self.all_records: List[Dict[str, str]] = []
    
    def scroll_and_collect(self, days_back: Optional[int] = None) -> List[Dict[str, str]]:
        """Прокрутка страницы и сбор данных"""
        if days_back is None:
            logger.info("📊 Начинаем сбор ВСЕХ записей...")
            cutoff_date = None
        else:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            logger.info(f"📊 Начинаем сбор данных за последние {days_back} дней")
            logger.info(f"📅 Собираем записи с {cutoff_date.strftime('%d.%m.%Y')}")
        
        collected = 0
        previous_count = 0
        scroll_attempts = 0
        no_new_records_count = 0
        stop_collecting = False
        
        time.sleep(2)
        
        while scroll_attempts < self.config.scroll_attempts and not stop_collecting:
            try:
                items = self.parser.get_items()
                current_count = len(items)
                
                if current_count > previous_count:
                    new_count = current_count - previous_count
                    logger.info(f"📥 Найдено {new_count} новых записей (всего: {current_count})")
                    
                    for i in range(previous_count, current_count):
                        try:
                            record = self.parser.extract_record_from_item(items[i])
                            
                            if record and record.get('serial_number') and record.get('date_from'):
                                if cutoff_date:
                                    record_date = self.parser.parse_date(record.get('date_from', ''))
                                    if record_date and record_date < cutoff_date:
                                        logger.info(f"⏹️ Достигнута дата {record_date.strftime('%d.%m.%Y')}")
                                        stop_collecting = True
                                        break
                                
                                self.all_records.append(record)
                                collected += 1
                                
                                if collected % 10 == 0:
                                    logger.info(f"  ✅ Запись #{collected}: {record.get('fio', 'Без ФИО')[:30]}...")
                        except Exception as e:
                            logger.error(f"⚠️ Ошибка при обработке записи {i+1}: {e}")
                    
                    previous_count = current_count
                    no_new_records_count = 0
                else:
                    no_new_records_count += 1
                    logger.info(f"⏳ Ожидание загрузки... ({no_new_records_count}/10)")
                    
                    if no_new_records_count >= 10:
                        logger.info("✅ Все записи загружены!")
                        break
                
                if stop_collecting:
                    break
                
                logger.info(f"📜 Прокрутка страницы вниз (попытка {scroll_attempts + 1})...")
                
                try:
                    if items:
                        last_item = items[-1]
                        self.browser.execute_script("arguments[0].scrollIntoView(true);", last_item)
                        self.browser.execute_script("window.scrollBy(0, 500);")
                    else:
                        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                except:
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                time.sleep(self.config.scroll_wait)
                scroll_attempts += 1
                
                if len(self.all_records) > 0 and len(self.all_records) % 50 == 0:
                    logger.info(f"📊 Прогресс: собрано {len(self.all_records)} записей")
                    
            except Exception as e:
                logger.error(f"⚠️ Ошибка при сборе данных: {e}")
                time.sleep(1)
                scroll_attempts += 1
        
        logger.info(f"📊 Итого собрано записей: {len(self.all_records)}")
        return self.all_records
    
def save_to_json(self, records: List[Dict[str, str]] = None, filename: str = None) -> str:
    """
    Сохранить данные в JSON файл.
    Если filename не указан — перезаписывает ОДИН файл records.json
    """
    if records is None:
        records = self.all_records
    
    # Создаем папку output если её нет
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Если filename передан — используем его, иначе ПЕРЕЗАПИСЫВАЕМ records.json
    if filename:
        filepath = os.path.join(output_dir, filename)
    else:
        filepath = os.path.join(output_dir, 'records.json')
    
    # Подготавливаем данные с метаданными
    data = {
        "metadata": {
            "parsed_at": datetime.now().isoformat(),
            "total_records": len(records),
            "version": "1.0.0",
            "source": os.getenv("TARGET_URL"),
        },
        "records": records
    }
    
    # Сохраняем в JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ JSON файл сохранен: {filepath}")
    return filepath