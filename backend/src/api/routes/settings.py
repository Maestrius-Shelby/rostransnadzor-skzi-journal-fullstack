"""
API роуты для настроек
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio

from ..models.schemas import SettingsModel
from ..services.parser_service import parser_service

# router = APIRouter(prefix="/api", tags=["settings"])

router = APIRouter(tags=["settings"])

# Инициализируем настройки по умолчанию
if not hasattr(parser_service, 'settings'):
    parser_service.settings = {
        "auto_parse": True,
        "auto_parse_time": "12:00",
        "days_back": None,
        "headless": True,
        "export_path": "./output",
    }


@router.post("/")
async def update_settings(settings: SettingsModel):
    """Обновить настройки"""
    try:
        # Сохраняем настройки в сервисе
        parser_service.settings = {
            "auto_parse": settings.auto_parse,
            "auto_parse_time": settings.auto_parse_time,
            "days_back": settings.days_back,
            "headless": settings.headless,
            "export_path": settings.export_path,
        }
        
        # Если автоматический парсинг включен, перезапускаем планировщик
        if settings.auto_parse:
            try:
                parser_service.reschedule_daily_parser(settings.auto_parse_time)
            except Exception as e:
                print(f"⚠️ Ошибка перепланирования: {e}")
        
        return {
            "message": "Настройки сохранены",
            "settings": parser_service.settings
        }
    except Exception as e:
        print(f"❌ Error in update_settings: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_settings():
    """Получить настройки"""
    try:
        if hasattr(parser_service, 'settings'):
            return parser_service.settings
        return {
            "auto_parse": True,
            "auto_parse_time": "12:00",
            "days_back": None,
            "headless": True,
            "export_path": "./output",
        }
    except Exception as e:
        print(f"❌ Error in get_settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))