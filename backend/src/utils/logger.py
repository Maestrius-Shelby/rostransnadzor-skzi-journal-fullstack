"""
Настройка логирования для проекта
"""
import logging
import sys


def setup_logger(name: str = "rostransnadzor_parser", level=logging.INFO):
    """Настройка логгера"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Формат
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчик
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "rostransnadzor_parser"):
    """Получение логгера"""
    return logging.getLogger(name)