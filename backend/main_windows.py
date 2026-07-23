"""
Главный файл для запуска парсера
"""
import sys
import os
import json
import asyncio
import time
from datetime import datetime, timedelta

# Добавляем src в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import AppConfig
from src.core.browser_manager import BrowserManager
from src.recognition.template_manager import TemplateManager
from src.recognition.image_recognizer import ImageRecognizer
from src.navigation.click_actions import ClickActions
from src.parsing.data_parser import DataParser
from src.parsing.scroll_manager import ScrollManager
from src.export.excel_exporter import ExcelExporter
from src.utils.logger import setup_logger, get_logger

# Настройка логгера
setup_logger()
logger = get_logger(__name__)


def load_json_data(filepath: str) -> list:
    """Загрузить данные из JSON файла"""
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
    """Запуск FastAPI сервера"""
    import uvicorn
    from src.api.main import app
    
    print("\n" + "="*60)
    print("🚀 ЗАПУСК API СЕРВЕРА")
    print("="*60 + "\n")
    print("📡 API доступен по адресу: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/api/ws")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


def load_data_to_api_service(records: list):
    """Загрузить данные в API сервис"""
    try:
        from src.api.services.parser_service import parser_service
        
        # Загружаем записи
        parser_service.records = records
        
        # Обновляем флаги
        today = datetime.now().date()
        for record in parser_service.records:
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to']
                    if ', ' in date_to_str:
                        date_to_str = date_to_str.split(', ')[0]
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    days_left = (date_to - today).days
                    record['days_left'] = days_left
                    record['is_expiring'] = 0 <= days_left <= 15
                    record['is_expired'] = days_left < 0
                except:
                    pass
        
        parser_service.total_records = len(parser_service.records)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки в API сервис: {e}")
        return False


def test_with_json():
    """Тестирование фронтенда с загруженным JSON файлом"""
    print("\n" + "="*60)
    print("🧪 РЕЖИМ ТЕСТИРОВАНИЯ")
    print("="*60 + "\n")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    
    if not os.path.exists(output_dir):
        print("❌ Папка output не найдена!")
        print("📁 Сначала запустите парсер (режим 1) или API сервер (режим 2)")
        return
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    if not json_files:
        print("❌ JSON файлы не найдены в папке output!")
        print("📁 Сначала запустите парсер (режим 1) или API сервер (режим 2)")
        return
    
    print("📂 Доступные JSON файлы:")
    for i, file in enumerate(json_files, 1):
        filepath = os.path.join(output_dir, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data.get('records', [])) if isinstance(data, dict) else len(data)
                date = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M')
                print(f"  {i}. {file} ({count} записей, {date_str})")
        except Exception as e:
            print(f"  {i}. {file} (ошибка чтения: {str(e)[:30]})")
    
    choice = input("\nВыберите номер файла для загрузки (или 'q' для выхода): ").strip()
    
    if choice.lower() == 'q':
        print("👋 Выход")
        return
    
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(json_files):
            print("❌ Неверный выбор!")
            return
        
        filepath = os.path.join(output_dir, json_files[idx])
        records = load_json_data(filepath)
        
        if not records:
            print("❌ Не удалось загрузить данные из файла")
            return
        
        print(f"\n✅ Загружено {len(records)} записей")
        
        # Обновляем флаги, НО СОХРАНЯЕМ is_new из файла
        today = datetime.now().date()
        for record in records:
            # Если is_new нет в файле - устанавливаем как True
            if 'is_new' not in record:
                record['is_new'] = True
            
            # Если is_mock нет в файле - устанавливаем как False
            if 'is_mock' not in record:
                record['is_mock'] = False
            
            # Обновляем флаги истечения
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to']
                    if ', ' in date_to_str:
                        date_to_str = date_to_str.split(', ')[0]
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    days_left = (date_to - today).days
                    record['days_left'] = days_left
                    record['is_expiring'] = 0 <= days_left <= 15
                    record['is_expired'] = days_left < 0
                except:
                    pass
        
        print("\n📤 Загрузка данных в API сервис...")
        
        try:
            from src.api.services.parser_service import parser_service
            
            # Полностью заменяем записи в сервисе
            parser_service.records = records
            parser_service.total_records = len(records)
            
            # Сохраняем в файл, чтобы флаги сохранились
            parser_service._save_records()
            
            new_count = len([r for r in parser_service.records if r.get('is_new', False)])
            expiring_count = len([r for r in parser_service.records if r.get('is_expiring', False)])
            expired_count = len([r for r in parser_service.records if r.get('is_expired', False)])
            mock_count = len([r for r in parser_service.records if r.get('is_mock', False)])
            
            print(f"\n✅ Данные загружены в API сервис!")
            print(f"📊 Всего записей: {len(parser_service.records)}")
            print(f"🟢 Новых (из JSON): {new_count}")
            print(f"🟠 Истекают (до 15 дней): {expiring_count}")
            print(f"🔴 Истекших: {expired_count}")
            print(f"🔵 Имитированных: {mock_count}")
            print(f"\n🚀 Теперь запустите API сервер (режим 2) и фронтенд")
            
        except Exception as e:
            print(f"⚠️ Ошибка загрузки в API сервис: {e}")
            print("💡 Но файл JSON сохранен и доступен для просмотра")
        
        print("\n📁 Путь к файлу:")
        print(f"   {filepath}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        

def run_imitation():
    """
    Запуск ИМИТАЦИИ парсинга с сравнением.
    Использует parser_service для тестирования логики сравнения записей.
    """
    import asyncio
    from src.api.services.parser_service import parser_service
    
    print("\n" + "="*60)
    print("🔄 ЗАПУСК ИМИТАЦИИ ПАРСИНГА (сравнение записей)")
    print("="*60 + "\n")
    
    async def run():
        try:
            # Показываем текущее состояние
            current_count = len(parser_service.records)
            new_count = parser_service.get_new_records_count()
            expiring_count = parser_service.get_expiring_records_count()
            expired_count = parser_service.get_expired_records_count()
            
            print(f"📊 Текущее состояние:")
            print(f"   📝 Всего записей: {current_count}")
            print(f"   🟢 Новых: {new_count}")
            print(f"   🟠 Истекающих: {expiring_count}")
            print(f"   🔴 Истекших: {expired_count}")
            print()
            
            # Запускаем имитацию
            print("🔄 Запуск имитации парсинга...")
            print("   (будет сгенерирован новый набор записей и выполненo сравнение)\n")
            
            await parser_service._mock_parse_with_comparison()
            
            print("\n" + "="*60)
            print("✅ ИМИТАЦИЯ ЗАВЕРШЕНА!")
            print("="*60)
            
            # Показываем результат
            new_count = parser_service.get_new_records_count()
            expiring_count = parser_service.get_expiring_records_count()
            expired_count = parser_service.get_expired_records_count()
            
            print(f"\n📊 Результат:")
            print(f"   📝 Всего записей: {len(parser_service.records)}")
            print(f"   🟢 Новых: {new_count}")
            print(f"   🟠 Истекающих: {expiring_count}")
            print(f"   🔴 Истекших: {expired_count}")
            
            if parser_service.last_files.get('excel'):
                print(f"\n📊 Excel: {parser_service.last_files['excel']}")
            if parser_service.last_files.get('json'):
                print(f"📄 JSON: {parser_service.last_files['json']}")
            
            # Показываем легенду цветов
            print(f"\n📋 Легенда цветов в Excel:")
            print(f"   🟢 Зеленый (берёзовый) - новые записи")
            print(f"   🟠 Оранжевый - истекают в ближайшие 15 дней")
            print(f"   🔴 Красный - истекшие (удалены с сайта)")
            
        except Exception as e:
            print(f"❌ Ошибка имитации: {e}")
            import traceback
            traceback.print_exc()
    
    # Запускаем асинхронную функцию
    asyncio.run(run())
    
    input("\nНажмите Enter для продолжения...")


def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ПАРСЕРА")
    print("="*60 + "\n")
    
    print("Выберите режим:")
    print("1 - Собрать ВСЕ данные (реальный парсинг)")
    print("2 - Запустить API сервер")
    print("3 - Тестировать фронтенд (загрузить JSON)")
    print("4 - ИМИТАЦИЯ парсинга (сравнение записей без браузера)")
    
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
        
        # Если choice == "1" или любой другой ввод - сбор всех данных
        if choice != "1":
            print("⚠️ Неверный выбор. Запускаем сбор всех данных (режим 1)...\n")
        
        # Загрузка конфигурации
        config = AppConfig()
        
        # Инициализация компонентов
        browser = BrowserManager(config.browser).setup()
        template_manager = TemplateManager()
        recognizer = ImageRecognizer(template_manager, confidence=0.5)
        click_actions = ClickActions(browser, recognizer)
        data_parser = DataParser(browser)
        scroll_manager = ScrollManager(browser, data_parser, config.parsing)
        
        # Авторизация
        browser.get(os.getenv("TARGET_URL"))
        
        if not click_actions.click_my_requests():
            logger.error("Не удалось найти пункт меню")
            return False
        
        if not click_actions.click_certificate_login():
            logger.error("Не удалось найти вход по сертификату")
            return False
        
        click_actions.click_select_certificate()
        click_actions.handle_cades_window()
        
        logger.info("Ожидание входа в личный кабинет...")
        time.sleep(8)
        
        # Сбор ВСЕХ данных (без ограничения по дням)
        logger.info("📊 Сбор ВСЕХ данных...")
        records = scroll_manager.scroll_and_collect(days_back=None)
        
        # Обновляем записи - добавляем флаги
        today = datetime.now().date()
        for record in records:
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to']
                    if ', ' in date_to_str:
                        date_to_str = date_to_str.split(', ')[0]
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    days_left = (date_to - today).days
                    record['days_left'] = days_left
                    record['is_expiring'] = 0 <= days_left <= 15
                    record['is_expired'] = days_left < 0
                    record['is_new'] = True
                except Exception as e:
                    logger.warning(f"Ошибка парсинга даты: {e}")
                    record['days_left'] = None
                    record['is_expiring'] = False
                    record['is_expired'] = False
                    record['is_new'] = True
            else:
                record['is_new'] = True
            record['is_mock'] = False
        
        # Экспорт
        if records:
            logger.info(f"Всего собрано записей: {len(records)}")
            
            # Сохраняем в JSON
            json_path = scroll_manager.save_to_json(records)
            logger.info(f"✅ JSON сохранен: {json_path}")
            
            # Сохраняем в Excel с подсветкой
            exporter = ExcelExporter(
                config.export,
                config.skzi_type,
                config.service_type,
                config.key_type
            )
            excel_path = exporter.export_to_excel(
                records,
                highlight_new=True,
                highlight_expiring=True,
                highlight_expired=True
            )
            logger.info(f"✅ Excel сохранен: {excel_path}")
            
            # Подсчет статистики
            new_count = len([r for r in records if r.get('is_new', False)])
            expiring_count = len([r for r in records if r.get('is_expiring', False)])
            expired_count = len([r for r in records if r.get('is_expired', False)])
            
            print(f"\n📊 СТАТИСТИКА:")
            print(f"  📝 Всего записей: {len(records)}")
            print(f"  🟢 Новых: {new_count}")
            print(f"  🟠 Истекают (до 15 дней): {expiring_count}")
            print(f"  🔴 Истекли: {expired_count}")
            print(f"\n📁 Файлы сохранены:")
            print(f"  📄 JSON: {json_path}")
            print(f"  📊 Excel: {excel_path}")
            
            if expiring_count > 0:
                print(f"\n⚠️ ВНИМАНИЕ: {expiring_count} записей истекают в ближайшие 15 дней!")
                print("   Они выделены оранжевым цветом в Excel и находятся в начале файла.")
        else:
            logger.warning("Нет данных для сохранения")
        
        print("\n" + "="*60)
        print("✅ ПАРСИНГ ЗАВЕРШЕН!")
        print("="*60)
        input("\nНажмите Enter для завершения...")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if browser:
            browser.close()


async def main_windows_with_progress(progress_callback=None, stop_callback=None, config=None):
    """
    Запуск парсера с колбэками для прогресса.
    Используется API сервером для реального парсинга.
    
    ✅ Все файлы перезаписываются: output/records.xlsx и output/records.json
    """
    from src.core.config import AppConfig
    from src.core.browser_manager import BrowserManager
    from src.recognition.template_manager import TemplateManager
    from src.recognition.image_recognizer import ImageRecognizer
    from src.navigation.click_actions import ClickActions
    from src.parsing.data_parser import DataParser
    from src.parsing.scroll_manager import ScrollManager
    from src.export.excel_exporter import ExcelExporter
    from src.utils.logger import setup_logger, get_logger
    
    setup_logger()
    logger = get_logger(__name__)
    
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
        
        browser = BrowserManager(app_config.browser).setup()
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
        
        if progress_callback:
            await progress_callback(20, 100, "Ожидание входа в ЛК...")
        
        wait_time = 12 if headless else 8
        time.sleep(wait_time)
        
        if progress_callback:
            await progress_callback(30, 100, "Сбор данных...")
        
        records = scroll_manager.scroll_and_collect(days_back=days_back)
        
        if not records:
            logger.warning("⚠️ Данные не собраны. Возможно, требуется ручная авторизация.")
            time.sleep(5)
            records = scroll_manager.scroll_and_collect(days_back=days_back)
        
        # Добавляем базовые флаги
        today = datetime.now().date()
        for record in records:
            if record.get('date_to'):
                try:
                    date_to_str = record['date_to']
                    if ', ' in date_to_str:
                        date_to_str = date_to_str.split(', ')[0]
                    date_to = datetime.strptime(date_to_str, '%d.%m.%Y').date()
                    days_left = (date_to - today).days
                    record['days_left'] = days_left
                    record['is_expiring'] = 0 <= days_left <= 15
                    record['is_expired'] = days_left < 0
                except:
                    record['days_left'] = None
                    record['is_expiring'] = False
                    record['is_expired'] = False
            record['is_mock'] = False
        
        if progress_callback:
            await progress_callback(90, 100, f"Собрано {len(records)} записей")
        
        if stop_callback and stop_callback():
            return []
        
        # ✅ Сохраняем в ЕДИНЫЕ файлы (перезаписываем)
        if records:
            # Путь к папке output в корне backend
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(backend_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # ✅ Единый Excel — перезаписывается
            excel_path = os.path.join(output_dir, 'records.xlsx')
            exporter = ExcelExporter(
                app_config.export,
                app_config.skzi_type,
                app_config.service_type,
                app_config.key_type
            )
            exporter.export_to_excel(
                records,
                highlight_new=True,
                highlight_expiring=True,
                highlight_expired=True,
                output_path=excel_path  # ← Перезаписываем один файл
            )
            logger.info(f"✅ Excel сохранен: {excel_path}")
            
            # ✅ Единый JSON — перезаписывается
            json_path = os.path.join(output_dir, 'records.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'parsed_at': datetime.now().isoformat(),
                        'total_records': len(records),
                        'version': '1.0.0',
                        'source': os.getenv("TARGET_URL"),
                    },
                    'records': records
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ JSON сохранен: {json_path}")
            
            new_count = len([r for r in records if r.get('is_new', False)])
            expiring_count = len([r for r in records if r.get('is_expiring', False)])
            expired_count = len([r for r in records if r.get('is_expired', False)])
            
            logger.info(f"📊 Статистика: Всего={len(records)}, Новых={new_count}, Истекающих={expiring_count}, Истекших={expired_count}")
            
            if progress_callback:
                await progress_callback(95, 100, f"Сохранено {len(records)} записей")
        
        if progress_callback:
            await progress_callback(100, 100, f"✅ Парсинг завершен! Собрано {len(records)} записей")
        
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