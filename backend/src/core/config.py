"""
Конфигурация приложения
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrowserConfig:
    """Конфигурация браузера"""
    yandex_path: str = r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe"
    headless: bool = False
    window_maximized: bool = True
    timeout: int = 10
    page_load_timeout: int = 30
    
    # ============================================
    # ДОБАВИТЬ ЭТИ НАСТРОЙКИ ДЛЯ HEADLESS
    # ============================================
    headless_window_width: int = 1920
    headless_window_height: int = 1080
    headless_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headless_timeout_multiplier: float = 2.0  # Увеличиваем таймауты в Headless режиме


@dataclass
class RecognitionConfig:
    """Конфигурация распознавания"""
    confidence_threshold: float = 0.5
    timeout: int = 10
    templates_dir: str = "assets"


@dataclass
class ParsingConfig:
    """Конфигурация парсинга"""
    days_back: int = 15
    max_records: int = 999999
    scroll_attempts: int = 100
    scroll_wait: float = 2.5
    
    # ============================================
    # ДОБАВИТЬ ДЛЯ HEADLESS
    # ============================================
    headless_scroll_wait: float = 4.0  # Увеличиваем задержку при скролле в Headless
    headless_scroll_attempts: int = 150  # Больше попыток в Headless


@dataclass
class ExportConfig:
    """Конфигурация экспорта"""
    excel_font: str = "Times New Roman"
    font_size: int = 11
    header_height: int = 60
    row_height: int = 25
    output_dir: str = "output"


@dataclass
class AppConfig:
    """Общая конфигурация приложения"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    recognition: RecognitionConfig = field(default_factory=RecognitionConfig)
    parsing: ParsingConfig = field(default_factory=ParsingConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    
    # Константы для Excel
    skzi_type: str = "КриптоПро CSP 5.0 ***** R3 *** ******-007671"
    service_type: str = "Установка ключевых документов"
    key_type: str = "ЭЦП"
    
    # ============================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С HEADLESS
    # ============================================
    def get_timeout(self) -> int:
        """Получить таймаут с учетом Headless режима"""
        if self.browser.headless:
            return int(self.browser.timeout * self.browser.headless_timeout_multiplier)
        return self.browser.timeout
    
    def get_page_load_timeout(self) -> int:
        """Получить таймаут загрузки страницы с учетом Headless режима"""
        if self.browser.headless:
            return int(self.browser.page_load_timeout * self.browser.headless_timeout_multiplier)
        return self.browser.page_load_timeout
    
    def get_scroll_wait(self) -> float:
        """Получить задержку при скролле с учетом Headless режима"""
        if self.browser.headless:
            return self.parsing.headless_scroll_wait
        return self.parsing.scroll_wait
    
    def get_scroll_attempts(self) -> int:
        """Получить количество попыток скролла с учетом Headless режима"""
        if self.browser.headless:
            return self.parsing.headless_scroll_attempts
        return self.parsing.scroll_attempts
    
    def get_window_size(self) -> tuple:
        """Получить размер окна с учетом Headless режима"""
        if self.browser.headless:
            return (self.browser.headless_window_width, self.browser.headless_window_height)
        return None  # Не устанавливаем размер в обычном режиме
    
    def get_user_agent(self) -> Optional[str]:
        """Получить User-Agent для Headless режима"""
        if self.browser.headless:
            return self.browser.headless_user_agent
        return None