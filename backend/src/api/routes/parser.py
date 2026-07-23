"""
API роуты для управления парсером
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import os

from ..models.schemas import (
    ParserStartRequest,
    ParserStopRequest,
    ParserStatusResponse
)
from ..services.parser_service import parser_service

router = APIRouter(tags=["parser"])

@router.get("/status")
async def get_status():
    """Получить статус парсера"""
    return parser_service.get_status()


@router.post("/start")
async def start_parser(request: ParserStartRequest):
    """Запустить парсер"""
    try:
        # Принимаем config как dict или None
        config = request.config if request.config else {}
        
        # Запускаем парсер
        result = await parser_service.start_parser(config)
        
        # Добавляем информацию о файлах
        if hasattr(parser_service, 'last_files') and parser_service.last_files:
            files = []
            
            if parser_service.last_files.get('json'):
                files.append(os.path.basename(parser_service.last_files['json']))
            if parser_service.last_files.get('excel'):
                files.append(os.path.basename(parser_service.last_files['excel']))
            if parser_service.last_files.get('csv'):
                files.append(os.path.basename(parser_service.last_files['csv']))
            
            if files:
                result['files'] = files
                result['json_path'] = parser_service.last_files.get('json')
                result['excel_path'] = parser_service.last_files.get('excel')
                result['csv_path'] = parser_service.last_files.get('csv')
        
        # Добавляем количество записей
        result['records_count'] = len(parser_service.records)
        
        return result
    except Exception as e:
        print(f"❌ Error in start_parser: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_parser(request: ParserStopRequest):
    """Остановить парсер"""
    try:
        result = await parser_service.stop_parser(request.force)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))