"""Domain models for LinkNower."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Type of workflow event."""

    BROWSER = "browser"
    COMMAND = "command"
    COMMIT = "commit"


class Event(BaseModel):
    """Represents a single workflow event (browsing, command, or commit)."""

    id: UUID = Field(default_factory=uuid4)
    type: EventType
    timestamp: datetime
    content: str
    metadata: dict[str, str] = Field(default_factory=dict)
    embedding_id: Optional[UUID] = None
    cluster_id: Optional[int] = None
    cwd: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: datetime | str | int) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        if isinstance(v, int):
            return datetime.fromtimestamp(v)
        raise ValueError(f"Invalid timestamp format: {v}")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Cluster(BaseModel):
    """Represents a cluster of related workflow events."""

    id: int
    label: str
    event_count: int
    start_time: datetime
    end_time: datetime
    representative_events: list[UUID] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_timestamp(cls, v: datetime | str | int) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        if isinstance(v, int):
            return datetime.fromtimestamp(v)
        raise ValueError(f"Invalid timestamp format: {v}")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Embedding(BaseModel):
    """Represents a semantic embedding vector."""

    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    vector: list[float]
    model: str
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_timestamp(cls, v: datetime | str | int) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        if isinstance(v, int):
            return datetime.fromtimestamp(v)
        raise ValueError(f"Invalid timestamp format: {v}")

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
