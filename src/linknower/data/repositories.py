"""Repository interfaces and implementations for data persistence."""

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import chromadb
from chromadb.config import Settings

from linknower.domain import Cluster, Embedding, Event, EventType


class EventRepository(ABC):
    """Abstract repository for Event persistence."""

    @abstractmethod
    def save(self, event: Event) -> None:
        """Save an event."""
        pass

    @abstractmethod
    def save_many(self, events: list[Event]) -> None:
        """Save multiple events efficiently."""
        pass

    @abstractmethod
    def get_by_id(self, event_id: UUID) -> Optional[Event]:
        """Get event by ID."""
        pass

    @abstractmethod
    def get_all(self) -> list[Event]:
        """Get all events."""
        pass

    @abstractmethod
    def get_by_type(self, event_type: EventType) -> list[Event]:
        """Get events by type."""
        pass

    @abstractmethod
    def get_by_time_range(self, start: datetime, end: datetime) -> list[Event]:
        """Get events within time range."""
        pass


class ClusterRepository(ABC):
    """Abstract repository for Cluster persistence."""

    @abstractmethod
    def save(self, cluster: Cluster) -> None:
        """Save a cluster."""
        pass

    @abstractmethod
    def get_by_id(self, cluster_id: int) -> Optional[Cluster]:
        """Get cluster by ID."""
        pass

    @abstractmethod
    def get_all(self) -> list[Cluster]:
        """Get all clusters."""
        pass


class EmbeddingRepository(ABC):
    """Abstract repository for Embedding persistence."""

    @abstractmethod
    def save(self, embedding: Embedding) -> None:
        """Save an embedding."""
        pass

    @abstractmethod
    def save_many(self, embeddings: list[Embedding]) -> None:
        """Save multiple embeddings efficiently."""
        pass

    @abstractmethod
    def search(self, query_vector: list[float], limit: int = 10) -> list[tuple[UUID, float]]:
        """Search for similar embeddings. Returns list of (event_id, similarity_score)."""
        pass


class SQLiteEventRepository(EventRepository):
    """SQLite implementation of EventRepository."""

    def __init__(self, db_path: Path):
        """Initialize repository with database path."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL,
                embedding_id TEXT,
                cluster_id INTEGER,
                cwd TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_cluster ON events(cluster_id)")
        conn.commit()
        conn.close()

    def save(self, event: Event) -> None:
        """Save an event."""
        self.save_many([event])

    def save_many(self, events: list[Event]) -> None:
        """Save multiple events efficiently."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.executemany(
            """
            INSERT OR REPLACE INTO events
            (id, type, timestamp, content, metadata, embedding_id, cluster_id, cwd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(e.id),
                    e.type.value,
                    e.timestamp.isoformat(),
                    e.content,
                    json.dumps(e.metadata),
                    str(e.embedding_id) if e.embedding_id else None,
                    e.cluster_id,
                    e.cwd,
                )
                for e in events
            ],
        )
        conn.commit()
        conn.close()

    def get_by_id(self, event_id: UUID) -> Optional[Event]:
        """Get event by ID."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        row = cursor.execute("SELECT * FROM events WHERE id = ?", (str(event_id),)).fetchone()
        conn.close()

        if not row:
            return None

        return Event(
            id=UUID(row["id"]),
            type=EventType(row["type"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            content=row["content"],
            metadata=json.loads(row["metadata"]),
            embedding_id=UUID(row["embedding_id"]) if row["embedding_id"] else None,
            cluster_id=int.from_bytes(row["cluster_id"], "little") if isinstance(row["cluster_id"], bytes) else row["cluster_id"],
            cwd=row["cwd"],
        )

    def get_all(self) -> list[Event]:
        """Get all events."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute("SELECT * FROM events ORDER BY timestamp").fetchall()
        conn.close()

        return [
            Event(
                id=UUID(row["id"]),
                type=EventType(row["type"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                embedding_id=UUID(row["embedding_id"]) if row["embedding_id"] else None,
                cluster_id=int.from_bytes(row["cluster_id"], "little") if isinstance(row["cluster_id"], bytes) else row["cluster_id"],
                cwd=row["cwd"],
            )
            for row in rows
        ]

    def get_by_type(self, event_type: EventType) -> list[Event]:
        """Get events by type."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute(
            "SELECT * FROM events WHERE type = ? ORDER BY timestamp", (event_type.value,)
        ).fetchall()
        conn.close()

        return [
            Event(
                id=UUID(row["id"]),
                type=EventType(row["type"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                embedding_id=UUID(row["embedding_id"]) if row["embedding_id"] else None,
                cluster_id=int.from_bytes(row["cluster_id"], "little") if isinstance(row["cluster_id"], bytes) else row["cluster_id"],
                cwd=row["cwd"],
            )
            for row in rows
        ]

    def get_by_time_range(self, start: datetime, end: datetime) -> list[Event]:
        """Get events within time range."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute(
            "SELECT * FROM events WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        conn.close()

        return [
            Event(
                id=UUID(row["id"]),
                type=EventType(row["type"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                content=row["content"],
                metadata=json.loads(row["metadata"]),
                embedding_id=UUID(row["embedding_id"]) if row["embedding_id"] else None,
                cluster_id=int.from_bytes(row["cluster_id"], "little") if isinstance(row["cluster_id"], bytes) else row["cluster_id"],
                cwd=row["cwd"],
            )
            for row in rows
        ]


class SQLiteClusterRepository(ClusterRepository):
    """SQLite implementation of ClusterRepository."""

    def __init__(self, db_path: Path):
        """Initialize repository with database path."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clusters (
                id INTEGER PRIMARY KEY,
                label TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                representative_events TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save(self, cluster: Cluster) -> None:
        """Save a cluster."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT OR REPLACE INTO clusters
            (id, label, event_count, start_time, end_time, representative_events, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cluster.id,
                cluster.label,
                cluster.event_count,
                cluster.start_time.isoformat(),
                cluster.end_time.isoformat(),
                json.dumps([str(e) for e in cluster.representative_events]),
                json.dumps(cluster.metadata),
            ),
        )
        conn.commit()
        conn.close()

    def get_by_id(self, cluster_id: int) -> Optional[Cluster]:
        """Get cluster by ID."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        row = cursor.execute("SELECT * FROM clusters WHERE id = ?", (cluster_id,)).fetchone()
        conn.close()

        if not row:
            return None

        return Cluster(
            id=row["id"],
            label=row["label"],
            event_count=row["event_count"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]),
            representative_events=[UUID(e) for e in json.loads(row["representative_events"])],
            metadata=json.loads(row["metadata"]),
        )

    def get_all(self) -> list[Cluster]:
        """Get all clusters."""
        import json

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute("SELECT * FROM clusters ORDER BY start_time").fetchall()
        conn.close()

        return [
            Cluster(
                id=row["id"],
                label=row["label"],
                event_count=row["event_count"],
                start_time=datetime.fromisoformat(row["start_time"]),
                end_time=datetime.fromisoformat(row["end_time"]),
                representative_events=[UUID(e) for e in json.loads(row["representative_events"])],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]


class ChromaDBEmbeddingRepository(EmbeddingRepository):
    """ChromaDB implementation of EmbeddingRepository."""

    def __init__(self, persist_directory: Path):
        """Initialize repository with ChromaDB persist directory."""
        self.persist_directory = persist_directory
        self.client = chromadb.Client(
            Settings(
                persist_directory=str(persist_directory),
                anonymized_telemetry=False,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="embeddings",
            metadata={"hnsw:space": "cosine"},
        )

    def save(self, embedding: Embedding) -> None:
        """Save an embedding."""
        self.save_many([embedding])

    def save_many(self, embeddings: list[Embedding]) -> None:
        """Save multiple embeddings efficiently."""
        if not embeddings:
            return

        self.collection.add(
            ids=[str(e.event_id) for e in embeddings],
            embeddings=[e.vector for e in embeddings],
            metadatas=[
                {
                    "embedding_id": str(e.id),
                    "model": e.model,
                    "created_at": e.created_at.isoformat(),
                }
                for e in embeddings
            ],
        )

    def search(self, query_vector: list[float], limit: int = 10) -> list[tuple[UUID, float]]:
        """Search for similar embeddings."""
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
        )

        if not results["ids"] or not results["distances"]:
            return []

        # ChromaDB returns distances (lower is better for cosine)
        # Convert to similarity scores (higher is better)
        return [
            (UUID(event_id), 1.0 - distance)
            for event_id, distance in zip(results["ids"][0], results["distances"][0])
        ]
