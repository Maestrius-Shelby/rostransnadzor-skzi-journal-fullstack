"""
Кастомные исключения для проекта
"""


class RoskaznaParserError(Exception):
    """Базовое исключение парсера"""
    pass


class BrowserSetupError(RoskaznaParserError):
    """Ошибка настройки браузера"""
    pass


class NavigationError(RoskaznaParserError):
    """Ошибка навигации"""
    pass


class RecognitionError(RoskaznaParserError):
    """Ошибка распознавания изображений"""
    pass


class ParsingError(RoskaznaParserError):
    """Ошибка парсинга данных"""
    pass


class ExportError(RoskaznaParserError):
    """Ошибка экспорта данных"""
    pass