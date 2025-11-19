"""Tests for domain models."""

from datetime import datetime
from uuid import uuid4

import pytest

from linknower.domain import Cluster, Embedding, Event, EventType


def test_event_creation():
    """Test Event model creation."""
    event = Event(
        type=EventType.BROWSER,
        timestamp=datetime.now(),
        content="Example.com - https://example.com",
        metadata={"url": "https://example.com", "title": "Example.com"},
    )

    assert event.id is not None
    assert event.type == EventType.BROWSER
    assert event.content == "Example.com - https://example.com"
    assert event.metadata["url"] == "https://example.com"


def test_cluster_creation():
    """Test Cluster model creation."""
    start = datetime.now()
    end = datetime.now()

    cluster = Cluster(
        id=1,
        label="Python Development",
        event_count=10,
        start_time=start,
        end_time=end,
        representative_events=[uuid4(), uuid4()],
    )

    assert cluster.id == 1
    assert cluster.label == "Python Development"
    assert cluster.event_count == 10
    assert len(cluster.representative_events) == 2


def test_embedding_creation():
    """Test Embedding model creation."""
    event_id = uuid4()
    vector = [0.1, 0.2, 0.3]

    embedding = Embedding(
        event_id=event_id,
        vector=vector,
        model="test-model",
    )

    assert embedding.id is not None
    assert embedding.event_id == event_id
    assert embedding.vector == vector
    assert embedding.model == "test-model"
