"""
API роуты для истории парсинга
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import json
import os

router = APIRouter(tags=["history"])

# Путь к файлу истории
HISTORY_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'history.json')


def _load_history():
    """Загрузить историю из файла"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def _save_history(history):
    """Сохранить историю в файл"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


@router.get("/history")
async def get_history(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """Получить историю парсинга"""
    history = _load_history()
    return history[offset:offset + limit]


@router.post("/history")
async def add_history_entry(entry: dict):
    """Добавить запись в историю"""
    history = _load_history()
    entry['timestamp'] = datetime.now().isoformat()
    history.insert(0, entry)
    _save_history(history)
    return {"status": "ok", "entry": entry}


@router.delete("/history")
async def clear_history():
    """Очистить историю"""
    _save_history([])
    return {"status": "ok"}


@router.delete("/history/{entry_id}")
async def delete_history_entry(entry_id: int):
    """Удалить запись из истории"""
    history = _load_history()
    if 0 <= entry_id < len(history):
        history.pop(entry_id)
        _save_history(history)
        return {"status": "ok"}
    raise HTTPException(404, "Запись не найдена")