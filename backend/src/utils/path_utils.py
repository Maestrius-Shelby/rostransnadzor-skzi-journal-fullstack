"""
Утилиты для работы с путями
"""
import os
import ctypes
import tempfile
import shutil


def get_short_path(path: str) -> str:
    """
    Получение короткого пути (8.3 формат) для Windows
    
    Args:
        path: Полный путь
        
    Returns:
        str: Короткий путь
    """
    try:
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetShortPathNameW(path, buffer, 260)
        return buffer.value if buffer.value else path
    except:
        return path


def get_project_root() -> str:
    """Получение корневой директории проекта"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_asset_path(filename: str, create_dir: bool = True) -> str:
    """
    Получение пути к файлу в папке assets с использованием короткого пути
    
    Args:
        filename: Имя файла
        create_dir: Создавать ли папку если её нет
        
    Returns:
        str: Полный путь к файлу (в коротком формате)
    """
    project_root = get_project_root()
    # Используем короткий путь для обхода проблем с кириллицей
    short_root = get_short_path(project_root)
    assets_dir = os.path.join(short_root, "assets")
    
    if create_dir and not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    return os.path.join(assets_dir, filename)


def get_output_path(filename: str) -> str:
    """
    Получение пути для выходных файлов
    
    Args:
        filename: Имя файла
        
    Returns:
        str: Полный путь к файлу
    """
    project_root = get_project_root()
    output_dir = os.path.join(project_root, "output")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    return os.path.join(output_dir, filename)


def get_asset_path_alternative(filename: str) -> str:
    """
    Альтернативный способ получения пути к файлу в папке assets
    с использованием временной копии
    
    Args:
        filename: Имя файла
        
    Returns:
        str: Путь к файлу во временной папке с латиницей
    """
    # Создаем временную папку с латиницей
    temp_dir = os.path.join(tempfile.gettempdir(), "roskazna_assets")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Путь к оригинальному файлу (с коротким путем)
    original_path = get_asset_path(filename)
    
    # Путь к временному файлу
    temp_path = os.path.join(temp_dir, filename)
    
    # Если оригинальный файл существует, копируем его во временную папку
    if os.path.exists(original_path):
        try:
            shutil.copy2(original_path, temp_path)
        except:
            pass
    
    return temp_path