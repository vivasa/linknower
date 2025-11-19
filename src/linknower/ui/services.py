"""Service factory for UI."""

from pathlib import Path

from linknower.data import (
    ChromaDBEmbeddingRepository,
    SQLiteClusterRepository,
    SQLiteEventRepository,
)
from linknower.ml import ClusteringEngine, EmbeddingEngine, FeatureEngineer
from linknower.services import (
    ClusterService,
    SearchService,
    StatsService,
    SyncService,
    TimelineService,
)
from linknower.utils import Config, PrivacyFilter


class ServiceFactory:
    """Factory for creating application services."""

    def __init__(self, config: Config):
        """Initialize factory with configuration."""
        self.config = config
        self._repositories = None
        self._ml_components = None
        self._services = None

    def get_services(self) -> dict:
        """Get all services, creating them if needed."""
        if self._services is None:
            self._initialize_repositories()
            self._initialize_ml_components()
            self._initialize_services()

        return self._services

    def _initialize_repositories(self) -> None:
        """Initialize data repositories."""
        self._repositories = {
            "event": SQLiteEventRepository(self.config.raw_db_path),
            "cluster": SQLiteClusterRepository(self.config.cluster_db_path),
            "embedding": ChromaDBEmbeddingRepository(self.config.chroma_db_path),
        }

    def _initialize_ml_components(self) -> None:
        """Initialize ML components."""
        self._ml_components = {
            "embedding_engine": EmbeddingEngine(self.config.embedding_model),
            "feature_engineer": FeatureEngineer(
                time_weight=self.config.time_weight,
                semantic_weight=self.config.semantic_weight,
                context_weight=self.config.context_weight,
            ),
            "clustering_engine": ClusteringEngine(
                min_cluster_size=self.config.min_cluster_size
            ),
        }

    def _initialize_services(self) -> None:
        """Initialize application services."""
        privacy_filter = PrivacyFilter(self.config.privacy_patterns)

        self._services = {
            "sync": SyncService(
                self._repositories["event"],
                self._repositories["embedding"],
                self._ml_components["embedding_engine"],
                privacy_filter,
                self.config,
            ),
            "search": SearchService(
                self._repositories["event"],
                self._repositories["embedding"],
                self._ml_components["embedding_engine"],
            ),
            "cluster": ClusterService(
                self._repositories["event"],
                self._repositories["cluster"],
                self._repositories["embedding"],
                self._ml_components["clustering_engine"],
                self._ml_components["feature_engineer"],
                self._ml_components["embedding_engine"],
            ),
            "timeline": TimelineService(self._repositories["event"]),
            "stats": StatsService(
                self._repositories["event"],
                self._repositories["cluster"],
            ),
        }

    def refresh_services(self) -> None:
        """Refresh services (useful after config changes)."""
        self._services = None
        self._ml_components = None
        self._repositories = None
        self.get_services()
