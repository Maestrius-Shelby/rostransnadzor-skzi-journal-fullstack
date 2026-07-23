"""
Парсер для Linux (altLinux)
Автоматический вход в личный кабинет
"""

import os
import sys
import json
import asyncio
import subprocess
import time
from datetime import datetime, timedelta

# Добавляем src в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import AppConfig, BrowserConfig
from src.core.browser_manager import BrowserManager
from src.recognition.template_manager import TemplateManager
from src.recognition.image_recognizer import ImageRecognizer
from src.navigation.click_actions import ClickActions
from src.parsing.data_parser import DataParser
from src.parsing.scroll_manager import ScrollManager
from src.export.excel_exporter import ExcelExporter
from src.utils.logger import setup_logger, get_logger
from src.utils.path_utils import get_project_root

setup_logger()
logger = get_logger(__name__)


# ============================================
# LINUX BROWSER CONFIG
# ============================================
class LinuxBrowserConfig(BrowserConfig):
    def __init__(self):
        super().__init__()
        self.chromium_path = self._find_browser()
        self.use_firefox = False

    def _find_browser(self) -> str:
        paths = [
            "/usr/bin/chromium-gost",
            "/usr/bin/chromium-gost-stable",
            "/usr/bin/yandex-browser-stable",
            "/usr/bin/yandex-browser",
            "/opt/yandex/browser/yandex-browser",
        ]
        for path in paths:
            if os.path.exists(path):
                logger.info(f"Найден браузер: {path}")
                return path
        for browser in ["chromium-gost", "yandex-browser", "chromium-browser"]:
            result = subprocess.run(["which", browser], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        raise FileNotFoundError("Браузер не найден!")


# ============================================
# LINUX BROWSER MANAGER
# ============================================
class LinuxBrowserManager(BrowserManager):
    def __init__(self, config: BrowserConfig):
        super().__init__(config)
        self.linux_config = config

    def _find_chromedriver(self) -> str:
        project_root = get_project_root()
        possible_paths = [
            os.path.join(project_root, "chromedriver-linux64", "chromedriver-linux64", "chromedriver"),
            os.path.join(project_root, "chromedriver-linux64", "chromedriver"),
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    os.chmod(path, 0o755)
                except:
                    pass
                logger.info(f"Найден ChromeDriver: {path}")
                return path
        raise FileNotFoundError("ChromeDriver не найден!")

    def setup(self) -> 'LinuxBrowserManager':
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait

        logger.info("Настройка WebDriver для Linux...")

        options = Options()
        if hasattr(self.linux_config, 'chromium_path') and self.linux_config.chromium_path:
            options.binary_location = self.linux_config.chromium_path

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        prefs = {
            "credentials_enable_service": True,
            "profile.password_manager_enabled": True,
        }
        options.add_experimental_option("prefs", prefs)

        chromedriver_path = self._find_chromedriver()
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)

        if self.config.window_maximized:
            self.driver.maximize_window()
        self.driver.set_page_load_timeout(self.config.page_load_timeout)
        self.wait = WebDriverWait(self.driver, self.config.timeout)
        logger.info("WebDriver для Linux готов")
        return self


# ============================================
# ОБЩИЕ ФУНКЦИИ
# ============================================
def load_json_data(filepath: str) -> list:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'records' in data:
        logger.info(f"📂 Загружено {len(data['records'])} записей из {filepath}")
        return data['records']
    if isinstance(data, list):
        logger.info(f"📂 Загружено {len(data)} записей из {filepath}")
        return data
    return []


def run_api():
    import uvicorn
    from src.api.main import app
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК API СЕРВЕРА")
    print("=" * 60 + "\n")
    print("📡 API доступен по адресу: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/api/ws")
    print("\n" + "=" * 60 + "\n")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)


def test_with_json():
    print("\n" + "=" * 60)
    print("🧪 РЕЖИМ ТЕСТИРОВАНИЯ")
    print("=" * 60 + "\n")

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    if not os.path.exists(output_dir):
        print("❌ Папка output не найдена!")
        return

    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print("❌ JSON файлы не найдены!")
        return

    print("📂 Доступные JSON файлы:")
    for i, file in enumerate(json_files, 1):
        filepath = os.path.join(output_dir, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data.get('records', [])) if isinstance(data, dict) else len(data)
                print(f"  {i}. {file} ({count} записей)")
        except:
            print(f"  {i}. {file} (ошибка чтения)")

    choice = input("\nВыберите номер (или 'q'): ").strip()
    if choice.lower() == 'q':
        return

    try:
        idx = int(choice) - 1
        filepath = os.path.join(output_dir, json_files[idx])
        records = load_json_data(filepath)
        if not records:
            return

        today = datetime.now().date()
        for record in records:
            if 'is_new' not in record:
                record['is_new'] = True
            if 'is_mock' not in record:
                record['is_mock'] = False
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to'].split(',')[0].strip()
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    record['days_left'] = (date_to - today).days
                    record['is_expiring'] = 0 <= record['days_left'] <= 15
                    record['is_expired'] = record['days_left'] < 0
                except:
                    pass

        from src.api.services.parser_service import parser_service
        parser_service.records = records
        parser_service.total_records = len(records)
        parser_service._save_records()
        print(f"\n✅ Загружено {len(records)} записей в API сервис!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def run_imitation():
    from src.api.services.parser_service import parser_service

    print("\n" + "=" * 60)
    print("🔄 ЗАПУСК ИМИТАЦИИ ПАРСИНГА")
    print("=" * 60 + "\n")

    async def run():
        print(f"📊 Текущее состояние: {len(parser_service.records)} записей")
        await parser_service._mock_parse_with_comparison()
        print("\n✅ ИМИТАЦИЯ ЗАВЕРШЕНА!")

    asyncio.run(run())
    input("\nНажмите Enter...")


# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================
def main():
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК ПАРСЕРА (Linux)")
    print("=" * 60 + "\n")
    print("1 - Собрать ВСЕ данные (реальный парсинг)")
    print("2 - Запустить API сервер")
    print("3 - Тестировать фронтенд (загрузить JSON)")
    print("4 - ИМИТАЦИЯ парсинга")

    choice = input("Ваш выбор (1/2/3/4): ").strip()
    browser = None

    try:
        if choice == "2":
            run_api()
            return True
        if choice == "3":
            test_with_json()
            return True
        if choice == "4":
            run_imitation()
            return True

        # Реальный парсинг
        config = AppConfig()
        browser_config = LinuxBrowserConfig()
        config.browser = browser_config
        browser = LinuxBrowserManager(config.browser).setup()

        template_manager = TemplateManager()
        recognizer = ImageRecognizer(template_manager, confidence=0.5)
        click_actions = ClickActions(browser, recognizer)
        data_parser = DataParser(browser)
        scroll_manager = ScrollManager(browser, data_parser, config.parsing)

        browser.get(os.getenv("TARGET_URL"))
        if not click_actions.click_my_requests():
            logger.error("Не удалось найти пункт меню")
            return False
        if not click_actions.click_certificate_login():
            logger.error("Не удалось найти вход по сертификату")
            return False

        click_actions.click_select_certificate()
        click_actions.handle_cades_window()
        logger.info("Ожидание входа...")
        time.sleep(8)

        records = scroll_manager.scroll_and_collect(days_back=None)

        today = datetime.now().date()
        for record in records:
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to'].split(',')[0].strip()
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    record['days_left'] = (date_to - today).days
                    record['is_expiring'] = 0 <= record['days_left'] <= 15
                    record['is_expired'] = record['days_left'] < 0
                except:
                    record['days_left'] = None
                    record['is_expiring'] = False
                    record['is_expired'] = False
            record['is_new'] = True
            record['is_mock'] = False

        if records:
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(backend_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)

            excel_path = os.path.join(output_dir, 'records.xlsx')
            exporter = ExcelExporter(config.export, config.skzi_type, config.service_type, config.key_type)
            exporter.export_to_excel(records, highlight_new=True, highlight_expiring=True, highlight_expired=True, output_path=excel_path)

            json_path = os.path.join(output_dir, 'records.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'records': records}, f, ensure_ascii=False, indent=2)

            print(f"\n✅ Сохранено {len(records)} записей\n📊 Excel: {excel_path}\n📄 JSON: {json_path}")

        print("\n✅ ПАРСИНГ ЗАВЕРШЕН!")
        input("\nНажмите Enter...")
        return True

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if browser:
            browser.close()


# ============================================
# ДЛЯ API СЕРВЕРА
# ============================================
async def main_linux_with_progress(progress_callback=None, stop_callback=None, config=None):
    from src.core.config import AppConfig

    browser = None
    try:
        app_config = AppConfig()
        days_back = None
        headless = False

        if config:
            if config.get('days_back'):
                days_back = config['days_back']
            if config.get('headless'):
                headless = config['headless']
                app_config.browser.headless = headless
                if headless:
                    app_config.browser.timeout = 60000
                    app_config.browser.page_load_timeout = 60000

        browser_config = LinuxBrowserConfig()
        app_config.browser = browser_config
        browser = LinuxBrowserManager(app_config.browser).setup()

        template_manager = TemplateManager()
        recognizer = ImageRecognizer(template_manager, confidence=0.5)
        click_actions = ClickActions(browser, recognizer)
        data_parser = DataParser(browser)
        scroll_manager = ScrollManager(browser, data_parser, app_config.parsing)

        if progress_callback:
            await progress_callback(0, 100, "Открытие сайта...")

        browser.get(os.getenv("TARGET_URL"))
        await asyncio.sleep(2)

        if not click_actions.click_my_requests():
            raise Exception("Не удалось найти пункт меню")
        if not click_actions.click_certificate_login():
            raise Exception("Не удалось найти вход по сертификату")

        if progress_callback:
            await progress_callback(10, 100, "Вход в систему...")

        click_actions.click_select_certificate()
        click_actions.handle_cades_window()

        wait_time = 12 if headless else 8
        time.sleep(wait_time)

        if progress_callback:
            await progress_callback(30, 100, "Сбор данных...")

        records = scroll_manager.scroll_and_collect(days_back=days_back)

        if not records:
            time.sleep(5)
            records = scroll_manager.scroll_and_collect(days_back=days_back)

        today = datetime.now().date()
        for record in records:
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to'].split(',')[0].strip()
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    record['days_left'] = (date_to - today).days
                    record['is_expiring'] = 0 <= record['days_left'] <= 15
                    record['is_expired'] = record['days_left'] < 0
                except:
                    record['days_left'] = None
                    record['is_expiring'] = False
                    record['is_expired'] = False
            record['is_mock'] = False

        if stop_callback and stop_callback():
            return []

        if records:
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(backend_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)

            exporter = ExcelExporter(app_config.export, app_config.skzi_type, app_config.service_type, app_config.key_type)
            exporter.export_to_excel(records, highlight_new=True, highlight_expiring=True, highlight_expired=True,
                                     output_path=os.path.join(output_dir, 'records.xlsx'))
            with open(os.path.join(output_dir, 'records.json'), 'w', encoding='utf-8') as f:
                json.dump({'records': records}, f, ensure_ascii=False, indent=2)

        if progress_callback:
            await progress_callback(100, 100, f"✅ Собрано {len(records)} записей")

        return records

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        if progress_callback:
            await progress_callback(0, 100, f"❌ Ошибка: {str(e)}")
        raise
    finally:
        if browser:
            browser.close()


if __name__ == "__main__":
    main()