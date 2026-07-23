"""
Распознавание изображений на экране
"""
import time
import os
from typing import Optional, Tuple
import cv2
import numpy as np
import pyautogui
import mss

from ..utils.logger import get_logger
from ..utils.path_utils import get_short_path
from .template_manager import TemplateManager

logger = get_logger(__name__)


class ImageRecognizer:
    """Распознавание изображений на экране"""
    
    def __init__(self, template_manager: TemplateManager, confidence: float = 0.5):
        self.template_manager = template_manager
        self.confidence = confidence
    
    def find_and_click(
        self,
        template_name: str,
        confidence: Optional[float] = None,
        timeout: int = 10,
        click_offset: Tuple[int, int] = (0, 0)
    ) -> bool:
        """Поиск изображения на экране и клик по нему"""
        confidence = confidence or self.confidence
        
        logger.info(f"Ищем изображение: {template_name}")
        
        template_path = self.template_manager.get_template_path(template_name)
        if not template_path or not os.path.exists(template_path):
            logger.error(f"Шаблон не найден: {template_name}")
            return False
        
        # Пробуем загрузить через короткий путь (обход кириллицы)
        short_path = get_short_path(template_path)
        template = cv2.imread(short_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None:
            # Пробуем через обычный путь
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None:
            logger.error(f"Не удалось загрузить шаблон: {template_path}")
            return False
        
        template_height, template_width = template.shape
        
        start_time = time.time()
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            
            while time.time() - start_time < timeout:
                screenshot = sct.grab(monitor)
                screenshot_np = np.array(screenshot)
                screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)
                
                result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= confidence:
                    center_x = max_loc[0] + template_width // 2 + click_offset[0]
                    center_y = max_loc[1] + template_height // 2 + click_offset[1]
                    
                    logger.info(f"Найдено! Уверенность: {max_val:.3f}, координаты: ({center_x}, {center_y})")
                    pyautogui.click(center_x, center_y)
                    logger.info("Клик выполнен")
                    return True
                
                time.sleep(0.3)
        
        logger.warning(f"Изображение не найдено за {timeout} секунд")
        return False
    
    def press_enter(self) -> bool:
        """Нажатие Enter"""
        logger.info("Пробуем нажать Enter...")
        
        try:
            import keyboard
            keyboard.press_and_release('enter')
            logger.info("Enter нажат через keyboard")
            return True
        except:
            pass
        
        try:
            pyautogui.press('enter')
            logger.info("Enter нажат через pyautogui")
            return True
        except:
            pass
        
        return False