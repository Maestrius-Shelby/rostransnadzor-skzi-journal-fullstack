"""
Pydantic модели для API
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def dict(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    class Field:
        def __init__(self, *args, **kwargs):
            pass


class ParserStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


class ParserConfig(BaseModel):
    days_back: Optional[int] = None  # None = все данные
    max_records: int = 999999
    headless: bool = False
    confidence_threshold: float = 0.5
    mock: bool = False  # Режим имитации
    auto: bool = False  # Автоматический запуск


class ParserStartRequest(BaseModel):
    config: Optional[Dict[str, Any]] = None  # Принимаем любой dict


class ParserStopRequest(BaseModel):
    force: bool = False


class ParserStatusResponse(BaseModel):
    status: str = "idle"
    progress: float = 0.0
    total_records: int = 0
    current_record: int = 0
    message: Optional[str] = None
    is_running: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExportRequest(BaseModel):
    format: str = "excel"
    filename: Optional[str] = None


class SettingsModel(BaseModel):
    """Модель настроек"""
    auto_parse: bool = True
    auto_parse_time: str = "12:00"
    days_back: Optional[int] = None  # None = все данные
    headless: bool = True
    export_path: str = "./output"


class Record(BaseModel):
    """Модель записи"""
    id: Optional[int] = None
    date_from: str = ""
    skzi_type: str = ""
    service_type: str = ""
    fio: str = ""
    date_to: str = ""
    key_type: str = ""
    serial_number: str = ""
    key_carrier_number: str = ""
    destruction_date: str = ""
    destruction_signature: str = ""
    notes: str = ""
    is_new: bool = False
    is_expiring: bool = False
    is_expired: bool = False
    is_mock: bool = False
    days_left: Optional[int] = None
    created_at: Optional[datetime] = None


class HistoryEntry(BaseModel):
    """Модель записи истории"""
    id: Optional[int] = None
    type: str = ""
    startTime: str = ""
    endTime: str = ""
    duration: str = ""
    status: str = ""
    recordsCount: int = 0
    daysBack: Optional[int] = None
    headless: bool = False
    files: Optional[List[str]] = None
    error: Optional[str] = None
    format: Optional[str] = None