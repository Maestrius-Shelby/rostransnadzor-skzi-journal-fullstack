"""
Действия с кликами
"""
import time
import pyautogui

from ..utils.logger import get_logger
from ..core.browser_manager import BrowserManager
from ..recognition.image_recognizer import ImageRecognizer

logger = get_logger(__name__)


class ClickActions:
    """Действия с кликами на странице"""
    
    def __init__(self, browser: BrowserManager, recognizer: ImageRecognizer):
        self.browser = browser
        self.recognizer = recognizer
        self.select_button_coords = (960, 640)
    
    def click_my_requests(self) -> bool:
        """Клик по пункту 'Мои запросы'"""
        logger.info("Поиск 'Мои запросы...'")
        
        js_script = """
        var items = document.querySelectorAll('span');
        for (var i = 0; i < items.length; i++) {
            if (items[i].textContent.includes('Мои запросы и отзыв сертификата')) {
                var parent = items[i].closest('div[class*="_menu-item"]');
                if (parent) {
                    parent.click();
                    return true;
                }
                items[i].click();
                return true;
            }
        }
        return false;
        """
        
        try:
            result = self.browser.execute_script(js_script)
            if result:
                logger.info("Кликнули по меню")
                time.sleep(2)
                return True
        except:
            pass
        
        logger.error("Не найден пункт меню")
        return False
    
    def click_certificate_login(self) -> bool:
        """Клик по 'Вход по сертификату'"""
        logger.info("Поиск 'Вход по сертификату'...")
        time.sleep(2)
        
        js_script = """
        var tiles = document.querySelectorAll('div[class*="_tile"]');
        for (var i = 0; i < tiles.length; i++) {
            if (tiles[i].textContent.includes('Вход по сертификату')) {
                tiles[i].click();
                return true;
            }
        }
        return false;
        """
        
        try:
            result = self.browser.execute_script(js_script)
            if result:
                logger.info("Кликнули по входу по сертификату")
                time.sleep(2)
                return True
        except:
            pass
        
        logger.error("Не найден 'Вход по сертификату'")
        return False
    
    def click_select_certificate(self) -> bool:
        """Нажатие кнопки 'Выбрать'"""
        logger.info("Нажимаем кнопку 'Выбрать'...")
        
        if self.recognizer.find_and_click("select_button.png", timeout=3):
            logger.info("Кликнули по кнопке 'Выбрать' через распознавание")
            time.sleep(1)
            return True
        
        logger.info("Используем координаты для клика")
        x, y = self.select_button_coords
        logger.info(f"Кликаем по координатам: ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(2)
        return True
    
    def handle_cades_window(self) -> bool:
        """Обработка окна CAdES"""
        logger.info("Ожидание окна CAdES...")
        time.sleep(3)
        
        if self.recognizer.find_and_click("ok_button.png", timeout=8):
            logger.info("Кнопка 'ОК' нажата через распознавание!")
            time.sleep(2)
            return True
        
        if self.recognizer.press_enter():
            logger.info("Enter нажат")
            time.sleep(2)
            return True
        
        logger.warning("Не удалось найти кнопку 'ОК' автоматически")
        input("Нажмите Enter после ручного нажатия 'ОК'...")
        return True