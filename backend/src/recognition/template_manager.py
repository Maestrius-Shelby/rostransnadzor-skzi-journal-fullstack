"""
Управление шаблонами для распознавания
"""
import os
from typing import Optional

from ..utils.path_utils import get_asset_path, get_short_path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TemplateManager:
    """Управление шаблонами изображений"""
    
    def __init__(self):
        self.templates: dict = {}
    
    def get_template_path(self, template_name: str) -> Optional[str]:
        """
        Получение пути к шаблону с использованием короткого пути
        
        Args:
            template_name: Имя шаблона (например, "ok_button.png")
            
        Returns:
            Optional[str]: Полный путь к файлу (в коротком формате)
        """
        # Получаем путь через get_asset_path (уже использует короткий путь)
        path = get_asset_path(template_name)
        
        if os.path.exists(path):
            return path
        
        # Проверяем через короткий путь
        short_path = get_short_path(path)
        if os.path.exists(short_path):
            return short_path
        
        logger.warning(f"Шаблон не найден: {path}")
        return None
    
    def list_templates(self) -> list:
        """Список доступных шаблонов"""
        assets_dir = os.path.dirname(get_asset_path(""))
        if os.path.exists(assets_dir):
            return [f for f in os.listdir(assets_dir) if f.endswith(('.png', '.jpg'))]
        return []