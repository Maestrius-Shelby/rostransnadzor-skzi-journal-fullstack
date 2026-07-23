"""
Парсинг данных со страницы
"""
from typing import Dict, Optional, List
from selenium.webdriver.common.by import By
from datetime import datetime

from ..utils.logger import get_logger
from ..core.browser_manager import BrowserManager

logger = get_logger(__name__)


class DataParser:
    """Парсинг данных со страницы"""
    
    def __init__(self, browser: BrowserManager):
        self.browser = browser
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки"""
        try:
            date_str = date_str.strip()
            return datetime.strptime(date_str, "%d.%m.%Y, %H:%M")
        except:
            try:
                return datetime.strptime(date_str, "%d.%m.%Y")
            except:
                return None
    
    def extract_record_from_item(self, item) -> Dict[str, str]:
        """Извлечение данных из элемента записи"""
        record = {}
        
        try:
            # Дата установки
            try:
                date_from_elem = item.find_element(By.CSS_SELECTOR, "p._date__from_ycb2i_47")
                record['date_from'] = date_from_elem.text.replace("от ", "").strip()
            except:
                record['date_from'] = ""
            
            # ФИО
            try:
                all_p = item.find_elements(By.TAG_NAME, "p")
                for p in all_p:
                    text = p.text.strip()
                    if (text and 
                        not text.startswith("от ") and 
                        not text.startswith("до ") and
                        not text.startswith("СНИЛС:") and
                        len(text) > 5 and
                        not text.isdigit() and
                        len(text) < 50):
                        record['fio'] = text
                        break
            except:
                record['fio'] = ""
            
            # Серийный номер
            try:
                info_divs = item.find_elements(By.CSS_SELECTOR, "div._info_ycb2i_37")
                for div in info_divs:
                    try:
                        p_text = div.find_element(By.TAG_NAME, "p").text.strip()
                        if not p_text.startswith("СНИЛС:") and len(p_text) > 10:
                            record['serial_number'] = p_text
                            break
                    except:
                        continue
            except:
                record['serial_number'] = ""
            
            # Срок действия
            try:
                date_to_elem = item.find_element(By.XPATH, ".//p[contains(text(), 'до ')]")
                record['date_to'] = date_to_elem.text.replace("до ", "").strip()
            except:
                record['date_to'] = ""
            
            return record
            
        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return {}
    
    def get_items(self) -> List:
        """Получение всех записей на странице"""
        return self.browser.find_elements(By.CSS_SELECTOR, "div._list-item_ycb2i_14")