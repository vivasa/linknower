"""Machine learning components for semantic search and clustering."""

from datetime import datetime
from typing import Optional

import hdbscan
import numpy as np
import umap
from sentence_transformers import SentenceTransformer

from linknower.domain import Cluster, Embedding, Event


class EmbeddingEngine:
    """Generates semantic embeddings for text content."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with sentence transformer model."""
        self.model_name = model_name
        # Force CPU execution to avoid tensor device issues
        self.model = SentenceTransformer(model_name, device="cpu")

    def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        # Explicitly disable tensor conversion and normalize
        embedding = self.model.encode(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True,
            device="cpu"
        )
        return embedding.tolist()

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts efficiently."""
        # Batch encoding with explicit CPU device and no tensor conversion
        embeddings = self.model.encode(
            texts,
            convert_to_tensor=False,
            normalize_embeddings=True,
            show_progress_bar=True,
            device="cpu",
            batch_size=32  # Reasonable batch size for CPU
        )
        return embeddings.tolist()

    def embed_event(self, event: Event) -> Embedding:
        """Generate embedding for an event."""
        vector = self.embed(event.content)
        return Embedding(
            event_id=event.id,
            vector=vector,
            model=self.model_name,
        )

    def embed_events(self, events: list[Event]) -> list[Embedding]:
        """Generate embeddings for multiple events efficiently."""
        texts = [e.content for e in events]
        vectors = self.embed_many(texts)

        return [
            Embedding(
                event_id=event.id,
                vector=vector,
                model=self.model_name,
            )
            for event, vector in zip(events, vectors)
        ]


class FeatureEngineer:
    """Combines multiple features for clustering."""

    def __init__(
        self,
        time_weight: float = 0.3,
        semantic_weight: float = 0.5,
        context_weight: float = 0.2,
    ):
        """Initialize with feature weights (must sum to 1.0)."""
        total = time_weight + semantic_weight + context_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

        self.time_weight = time_weight
        self.semantic_weight = semantic_weight
        self.context_weight = context_weight

    def combine_features(
        self,
        events: list[Event],
        embeddings: list[list[float]],
    ) -> np.ndarray:
        """Combine temporal, semantic, and contextual features."""
        n = len(events)
        if n != len(embeddings):
            raise ValueError("Events and embeddings must have same length")

        # Temporal features (normalized timestamps)
        timestamps = np.array([e.timestamp.timestamp() for e in events])
        time_features = (timestamps - timestamps.min()) / (timestamps.max() - timestamps.min() + 1e-6)
        time_features = time_features.reshape(-1, 1)

        # Semantic features (embeddings)
        semantic_features = np.array(embeddings)

        # Context features (one-hot encoded event types + CWD similarity)
        context_features = self._extract_context_features(events)

        # Normalize each feature type
        time_features = self._normalize(time_features)
        semantic_features = self._normalize(semantic_features)
        context_features = self._normalize(context_features)

        # Combine with weights
        combined = np.concatenate(
            [
                time_features * self.time_weight,
                semantic_features * self.semantic_weight,
                context_features * self.context_weight,
            ],
            axis=1,
        )

        return combined

    def _extract_context_features(self, events: list[Event]) -> np.ndarray:
        """Extract contextual features (event type + CWD)."""
        # One-hot encode event types
        type_features = np.zeros((len(events), 3))
        for i, event in enumerate(events):
            if event.type.value == "browser":
                type_features[i, 0] = 1
            elif event.type.value == "command":
                type_features[i, 1] = 1
            elif event.type.value == "commit":
                type_features[i, 2] = 1

        # CWD similarity (simple: same CWD = 1, different = 0)
        cwd_features = np.zeros((len(events), 1))
        cwds = [e.cwd for e in events]
        most_common_cwd = max(set(cwds), key=cwds.count) if cwds else None

        for i, event in enumerate(events):
            if event.cwd and event.cwd == most_common_cwd:
                cwd_features[i, 0] = 1

        return np.concatenate([type_features, cwd_features], axis=1)

    @staticmethod
    def _normalize(features: np.ndarray) -> np.ndarray:
        """Normalize features to [0, 1] range."""
        min_val = features.min(axis=0, keepdims=True)
        max_val = features.max(axis=0, keepdims=True)
        return (features - min_val) / (max_val - min_val + 1e-6)


class ClusteringEngine:
    """Performs density-based clustering on event features."""

    def __init__(
        self,
        n_neighbors: int = 15,
        min_cluster_size: int = 5,
        min_samples: Optional[int] = None,
    ):
        """Initialize clustering parameters."""
        self.n_neighbors = n_neighbors
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples or min_cluster_size

    def cluster(
        self,
        events: list[Event],
        features: np.ndarray,
    ) -> dict[int, list[Event]]:
        """Cluster events and return mapping of cluster_id -> events."""
        if len(events) < self.min_cluster_size:
            return {-1: events}  # All noise if too few events

        # Dimensionality reduction with UMAP
        reducer = umap.UMAP(
            n_neighbors=self.n_neighbors,
            n_components=5,
            metric="euclidean",
            random_state=42,
        )
        reduced_features = reducer.fit_transform(features)

        # Clustering with HDBSCAN
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric="euclidean",
        )
        labels = clusterer.fit_predict(reduced_features)

        # Group events by cluster
        clusters: dict[int, list[Event]] = {}
        for event, label in zip(events, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(event)

        return clusters

    def generate_cluster_summary(
        self,
        cluster_id: int,
        events: list[Event],
    ) -> Cluster:
        """Generate a cluster summary with label."""
        if not events:
            raise ValueError("Cannot generate summary for empty cluster")

        # Sort by timestamp
        events_sorted = sorted(events, key=lambda e: e.timestamp)

        # Generate label from most common terms
        label = self._generate_label(events_sorted)

        return Cluster(
            id=cluster_id,
            label=label,
            event_count=len(events),
            start_time=events_sorted[0].timestamp,
            end_time=events_sorted[-1].timestamp,
            representative_events=[e.id for e in events_sorted[:3]],  # Top 3 as representatives
            metadata={},
        )

    def _generate_label(self, events: list[Event]) -> str:
        """Generate a human-readable label for cluster."""
        from collections import Counter

        # Extract keywords from event content
        all_words = []
        for event in events:
            # Simple tokenization (split on non-alphanumeric)
            words = [w.lower() for w in event.content.split() if len(w) > 3]
            all_words.extend(words)

        # Count word frequencies
        if not all_words:
            return "Miscellaneous Activity"

        word_counts = Counter(all_words)
        top_words = [word for word, _ in word_counts.most_common(3)]

        # Create label
        if len(top_words) >= 2:
            return f"{top_words[0].title()} & {top_words[1].title()}"
        elif len(top_words) == 1:
            return top_words[0].title()
        else:
            return "Miscellaneous Activity"
