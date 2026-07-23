"""
Управление браузером и WebDriver
"""
import time
import os
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# Импорты из utils
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.logger import get_logger
from src.utils.exceptions import BrowserSetupError
from src.core.config import BrowserConfig

logger = get_logger(__name__)


class BrowserManager:
    """Управление браузером"""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
    
    def _find_chromedriver(self) -> str:
        """Поиск chromedriver.exe"""
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        possible_paths = [
            os.path.join(script_dir, "chromedriver.exe"),
            os.path.join(script_dir, "chromedriver-win64", "chromedriver.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Найден ChromeDriver: {path}")
                return path
        
        raise BrowserSetupError("chromedriver.exe не найден!")
    
    def setup(self) -> 'BrowserManager':
        """Настройка и запуск WebDriver"""
        logger.info("Настройка WebDriver...")
        
        options = Options()
        
        # Путь к браузеру
        if hasattr(self.config, 'yandex_path') and self.config.yandex_path:
            options.binary_location = self.config.yandex_path
        
        # ============================================
        # ДОБАВИТЬ ЭТОТ БЛОК - НАСТРОЙКИ ДЛЯ HEADLESS
        # ============================================
        if self.config.headless:
            logger.info("🔄 Запуск в Headless режиме")
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-logging')
            options.add_argument('--log-level=3')
            options.add_argument('--silent')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # ============================================
        
        # Основные настройки (для всех режимов)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--enable-plugins')
        
        # Настройки для сертификатов
        prefs = {
            "credentials_enable_service": True,
            "profile.password_manager_enabled": True,
            "client_certificate_portal": True,
            "download.default_directory": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "output"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Дополнительные настройки для Headless
        if self.config.headless:
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
        
        chromedriver_path = self._find_chromedriver()
        service = Service(chromedriver_path)
        
        # Настройки сервиса для Headless
        if self.config.headless:
            service.suppress_output = True
            service.verbose = False
        
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Установка user-agent для Headless режима
        if self.config.headless:
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
        
        if self.config.window_maximized and not self.config.headless:
            self.driver.maximize_window()
        elif self.config.headless:
            self.driver.set_window_size(1920, 1080)
        
        self.driver.set_page_load_timeout(self.config.page_load_timeout)
        self.wait = WebDriverWait(self.driver, self.config.timeout)
        
        logger.info("WebDriver готов")
        return self
    
    def get(self, url: str) -> None:
        """Открытие URL"""
        logger.info(f"Открываем: {url}")
        self.driver.get(url)
        # Увеличиваем время ожидания для Headless
        wait_time = 5 if self.config.headless else 3
        time.sleep(wait_time)
    
    def execute_script(self, script: str, *args) -> any:
        """Выполнение JavaScript"""
        return self.driver.execute_script(script, *args)
    
    def find_element(self, by, value):
        """Поиск элемента"""
        return self.driver.find_element(by, value)
    
    def find_elements(self, by, value):
        """Поиск элементов"""
        return self.driver.find_elements(by, value)
    
    def get_current_url(self) -> str:
        """Получение текущего URL"""
        return self.driver.current_url
    
    def take_screenshot(self, path: str) -> None:
        """Сохранение скриншота"""
        self.driver.save_screenshot(path)
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            logger.info("Браузер закрыт")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()