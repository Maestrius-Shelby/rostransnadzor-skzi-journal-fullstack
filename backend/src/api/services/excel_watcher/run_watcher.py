"""
Скрипт для запуска вотчера
Можно запускать отдельно: python -m src.services.excel_watcher.run_watcher
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from excel_watcher import ExcelWatcherService
from data_manager import DataManager
from src.core.config import settings


def main():
    """Точка входа для запуска вотчера"""
    
    # Инициализация data_manager если нужно
    data_manager = DataManager()  # или None если не требуется
    
    # Пути для наблюдения
    watch_paths = [
        # Excel файлы из парсера
        "output/",
        # Исходные файлы данных
        "data/",
        # Можно добавить конкретные файлы
        # "output/Журнал_СКЗИ_отчет.xlsx",
    ]
    
    # Путь для выходного JSON (который читает веб-интерфейс)
    json_output_path = "src/data/records.json"
    
    # Создаем и запускаем вотчер
    watcher = ExcelWatcherService(
        data_manager=data_manager,
        watch_paths=watch_paths,
        json_output_path=json_output_path,
        ws_host=settings.WS_HOST if hasattr(settings, 'WS_HOST') else 'localhost',
        ws_port=settings.WS_PORT if hasattr(settings, 'WS_PORT') else 8765
    )
    
    try:
        watcher.start()
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")


if __name__ == '__main__':
    main()