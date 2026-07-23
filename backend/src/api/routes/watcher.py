"""
API роуты для управления вотчером
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import os

router = APIRouter(tags=["watcher"])

# Будет установлено при инициализации из main.py
watcher_service = None


class WatcherPaths(BaseModel):
    """Конфигурация путей для вотчера"""
    watch_paths: List[str]
    json_output_path: str


class WatcherStatus(BaseModel):
    """Статус вотчера"""
    is_running: bool
    files_processed: int
    last_update: Optional[str]
    errors: int
    watch_paths: List[str]
    ws_clients: int


@router.get("/status")
async def get_watcher_status():
    """Получить статус вотчера"""
    if not watcher_service:
        raise HTTPException(404, "Вотчер не инициализирован")
    return watcher_service.get_stats()


@router.post("/start")
async def start_watcher():
    """Запустить вотчер"""
    if not watcher_service:
        raise HTTPException(500, "Вотчер не инициализирован")
    
    watcher_service.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_watcher():
    """Остановить вотчер"""
    if not watcher_service:
        raise HTTPException(500, "Вотчер не инициализирован")
    
    watcher_service.stop()
    return {"status": "stopped"}


@router.post("/restart")
async def restart_watcher():
    """Перезапустить вотчер"""
    if not watcher_service:
        raise HTTPException(500, "Вотчер не инициализирован")
    
    watcher_service.stop()
    watcher_service.start()
    return {"status": "restarted"}


@router.put("/paths")
async def update_watch_paths(config: WatcherPaths):
    """Обновить пути наблюдения"""
    if not watcher_service:
        raise HTTPException(500, "Вотчер не инициализирован")
    
    watcher_service.watch_paths = config.watch_paths
    watcher_service.json_output_path = config.json_output_path
    
    # Перезапускаем для применения изменений
    watcher_service.stop()
    watcher_service.start()
    
    return {
        "status": "updated",
        "watch_paths": config.watch_paths,
        "json_output_path": config.json_output_path
    }


@router.post("/process/{file_path:path}")
async def process_file(file_path: str):
    """Обработать конкретный файл"""
    if not watcher_service:
        raise HTTPException(500, "Вотчер не инициализирован")
    
    full_path = os.path.join(os.getcwd(), file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(404, f"Файл не найден: {full_path}")
    
    watcher_service.process_excel_file(full_path)
    
    return {
        "status": "processed",
        "file": file_path,
        "stats": watcher_service.get_stats()
    }


@router.get("/ws/info")
async def get_websocket_info():
    """Информация о WebSocket сервере"""
    if not watcher_service:
        raise HTTPException(404, "Вотчер не инициализирован")
    
    return {
        "ws_url": f"ws://{watcher_service.ws_manager.host}:{watcher_service.ws_manager.port}",
        "clients_count": len(watcher_service.ws_manager.clients),
        "is_running": watcher_service.is_running
    }


def set_watcher_service(service):
    """Установить сервис вотчера"""
    global watcher_service
    watcher_service = service