"""
Модели для работы с базами данных
PostgreSQL и ClickHouse
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DatabaseType(Enum):
    """Типы баз данных"""
    POSTGRES = "postgres"
    CLICKHOUSE = "clickhouse"


@dataclass
class Source:
    """Модель источника текста"""
    id: Optional[uuid.UUID] = None
    source_hash: str = ""
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    text: Optional[str] = None  # Первый килобайт текста для просмотра
    ingest_ts: Optional[datetime] = None
    force_recheck: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.id is None:
            self.id = uuid.uuid4()
        if self.ingest_ts is None:
            self.ingest_ts = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения в БД"""
        return {
            'id': str(self.id),
            'source_hash': self.source_hash,
            'source_url': self.source_url,
            'source_date': self.source_date,
            'text': self.text,
            'ingest_ts': self.ingest_ts,
            'force_recheck': self.force_recheck,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        """Создание объекта из словаря"""
        return cls(
            id=uuid.UUID(data['id']) if data.get('id') else None,
            source_hash=data['source_hash'],
            source_url=data.get('source_url'),
            source_date=data.get('source_date'),
            text=data.get('text'),
            ingest_ts=data.get('ingest_ts'),
            force_recheck=data.get('force_recheck', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


@dataclass
class Criterion:
    """Модель критерия анализа"""
    id: str = ""
    criterion_text: str = ""
    criteria_version: int = 1
    is_active: bool = True
    threshold: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения в БД"""
        return {
            'id': self.id,
            'criterion_text': self.criterion_text,
            'criteria_version': self.criteria_version,
            'is_active': self.is_active,
            'threshold': self.threshold,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Criterion':
        """Создание объекта из словаря"""
        return cls(
            id=data['id'],
            criterion_text=data['criterion_text'],
            criteria_version=data.get('criteria_version', 1),
            is_active=data.get('is_active', True),
            threshold=data.get('threshold'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


@dataclass
class Event:
    """Модель события анализа"""
    event_id: Optional[uuid.UUID] = None
    source_hash: str = ""
    source_url: Optional[str] = None
    source_date: Optional[datetime] = None
    ingest_ts: Optional[datetime] = None
    criterion_id: str = ""
    criterion_text: str = ""
    is_match: bool = False
    confidence: float = 0.0
    summary: str = ""
    model_name: str = ""
    latency_ms: int = 0
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.event_id is None:
            self.event_id = uuid.uuid4()
        if self.ingest_ts is None:
            self.ingest_ts = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения в БД"""
        return {
            'event_id': str(self.event_id),
            'source_hash': self.source_hash,
            'source_url': self.source_url,
            'source_date': self.source_date,
            'ingest_ts': self.ingest_ts,
            'criterion_id': self.criterion_id,
            'criterion_text': self.criterion_text,
            'is_match': 1 if self.is_match else 0,  # ClickHouse использует UInt8
            'confidence': self.confidence,
            'summary': self.summary,
            'model_name': self.model_name,
            'latency_ms': self.latency_ms,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Создание объекта из словаря"""
        return cls(
            event_id=uuid.UUID(data['event_id']) if data.get('event_id') else None,
            source_hash=data['source_hash'],
            source_url=data.get('source_url'),
            source_date=data.get('source_date'),
            ingest_ts=data.get('ingest_ts'),
            criterion_id=data['criterion_id'],
            criterion_text=data['criterion_text'],
            is_match=bool(data.get('is_match', 0)),
            confidence=float(data.get('confidence', 0.0)),
            summary=data.get('summary', ''),
            model_name=data.get('model_name', ''),
            latency_ms=int(data.get('latency_ms', 0)),
            created_at=data.get('created_at')
        )


@dataclass
class CriteriaStats:
    """Статистика по критериям"""
    criterion_id: str
    date: datetime
    total_events: int
    matches: int
    avg_confidence: float
    avg_latency_ms: float
    
    @property
    def match_rate(self) -> float:
        """Процент совпадений"""
        return (self.matches / self.total_events * 100) if self.total_events > 0 else 0.0


@dataclass
class SourceStats:
    """Статистика по источникам"""
    source_hash: str
    source_url: Optional[str]
    date: datetime
    total_events: int
    matches: int
    avg_confidence: float
    
    @property
    def match_rate(self) -> float:
        """Процент совпадений"""
        return (self.matches / self.total_events * 100) if self.total_events > 0 else 0.0
