"""Application services for orchestrating business logic."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from linknower.data import (
    ChromaDBEmbeddingRepository,
    ClusterRepository,
    CWDTracker,
    EmbeddingRepository,
    EventRepository,
    GitParser,
    SQLiteClusterRepository,
    SQLiteEventRepository,
    ZenBrowserParser,
    ZshHistoryParser,
)
from linknower.domain import Event, EventType
from linknower.ml import ClusteringEngine, EmbeddingEngine, FeatureEngineer
from linknower.utils import Config, PrivacyFilter


class SyncService:
    """Service for syncing data from various sources."""

    def __init__(
        self,
        event_repo: EventRepository,
        embedding_repo: EmbeddingRepository,
        embedding_engine: EmbeddingEngine,
        privacy_filter: PrivacyFilter,
        config: Config,
    ):
        """Initialize sync service."""
        self.event_repo = event_repo
        self.embedding_repo = embedding_repo
        self.embedding_engine = embedding_engine
        self.privacy_filter = privacy_filter
        self.config = config

    def sync_all(self, full: bool = False) -> dict[str, int]:
        """Sync data from all configured sources."""
        stats = {
            "browser": 0,
            "command": 0,
            "commit": 0,
        }

        # Sync browser history
        stats["browser"] = self.sync_browser(full)

        # Sync shell history
        stats["command"] = self.sync_shell(full)

        # Sync git repositories
        stats["commit"] = self.sync_git(full)

        return stats

    def sync_browser(self, full: bool = False) -> int:
        """Sync browser history."""
        profile_path = Path(self.config.zen_profile_path).expanduser()

        if not profile_path.exists():
            return 0

        parser = ZenBrowserParser(profile_path)
        events = []

        for event in parser.parse():
            # Apply privacy filter
            if not self.privacy_filter.is_allowed(event.content):
                continue

            events.append(event)

        # Save events and generate embeddings
        if events:
            self.event_repo.save_many(events)
            embeddings = self.embedding_engine.embed_events(events)
            self.embedding_repo.save_many(embeddings)

            # Update events with embedding IDs
            for event, embedding in zip(events, embeddings):
                event.embedding_id = embedding.id
            self.event_repo.save_many(events)

        return len(events)

    def sync_shell(self, full: bool = False) -> int:
        """Sync shell history."""
        history_path = Path(self.config.zsh_history_path).expanduser()

        if not history_path.exists():
            return 0

        cwd_tracker = CWDTracker(Path.home())
        parser = ZshHistoryParser(history_path, cwd_tracker)
        events = []

        for event in parser.parse():
            # Apply privacy filter
            if not self.privacy_filter.is_allowed(event.content):
                continue

            events.append(event)

        # Save events and generate embeddings
        if events:
            self.event_repo.save_many(events)
            embeddings = self.embedding_engine.embed_events(events)
            self.embedding_repo.save_many(embeddings)

            # Update events with embedding IDs
            for event, embedding in zip(events, embeddings):
                event.embedding_id = embedding.id
            self.event_repo.save_many(events)

        return len(events)

    def sync_git(self, full: bool = False) -> int:
        """Sync git repository commits."""
        total = 0

        for repo_path in self.config.git_repos:
            path = Path(repo_path).expanduser()
            if not path.exists():
                continue

            parser = GitParser(path)
            events = []

            for event in parser.parse():
                # Apply privacy filter
                if not self.privacy_filter.is_allowed(event.content):
                    continue

                events.append(event)

            # Save events and generate embeddings
            if events:
                self.event_repo.save_many(events)
                embeddings = self.embedding_engine.embed_events(events)
                self.embedding_repo.save_many(embeddings)

                # Update events with embedding IDs
                for event, embedding in zip(events, embeddings):
                    event.embedding_id = embedding.id
                self.event_repo.save_many(events)

                total += len(events)

        return total


class SearchService:
    """Service for semantic search over events."""

    def __init__(
        self,
        event_repo: EventRepository,
        embedding_repo: EmbeddingRepository,
        embedding_engine: EmbeddingEngine,
    ):
        """Initialize search service."""
        self.event_repo = event_repo
        self.embedding_repo = embedding_repo
        self.embedding_engine = embedding_engine

    def search(
        self,
        query: str,
        limit: int = 10,
        event_type: Optional[EventType] = None,
    ) -> list[tuple[Event, float]]:
        """Search for events semantically similar to query."""
        # Generate query embedding
        query_vector = self.embedding_engine.embed(query)

        # Search for similar embeddings
        results = self.embedding_repo.search(query_vector, limit=limit * 2)

        # Fetch events and filter by type if needed
        event_scores = []
        for event_id, score in results:
            event = self.event_repo.get_by_id(event_id)
            if event:
                if event_type is None or event.type == event_type:
                    event_scores.append((event, score))

        # Return top N after filtering
        return event_scores[:limit]


class ClusterService:
    """Service for clustering and analyzing workflow patterns."""

    def __init__(
        self,
        event_repo: EventRepository,
        cluster_repo: ClusterRepository,
        embedding_repo: EmbeddingRepository,
        clustering_engine: ClusteringEngine,
        feature_engineer: FeatureEngineer,
        embedding_engine: EmbeddingEngine,
    ):
        """Initialize cluster service."""
        self.event_repo = event_repo
        self.cluster_repo = cluster_repo
        self.embedding_repo = embedding_repo
        self.clustering_engine = clustering_engine
        self.feature_engineer = feature_engineer
        self.embedding_engine = embedding_engine

    def cluster_events(self) -> dict[str, int]:
        """Cluster all events and save clusters."""
        # Get all events
        events = self.event_repo.get_all()

        if len(events) < 5:
            return {"clusters": 0, "noise": len(events)}

        # Get embeddings for events (batch generate for efficiency)
        embeddings = self.embedding_engine.embed_many([e.content for e in events])
        valid_events = events

        if not valid_events:
            return {"clusters": 0, "noise": 0}

        # Combine features
        features = self.feature_engineer.combine_features(valid_events, embeddings)

        # Cluster
        clusters = self.clustering_engine.cluster(valid_events, features)

        # Save clusters (excluding noise cluster -1)
        num_clusters = 0
        noise_count = 0

        for cluster_id, cluster_events in clusters.items():
            if cluster_id == -1:
                noise_count = len(cluster_events)
                continue

            # Generate cluster summary
            cluster = self.clustering_engine.generate_cluster_summary(cluster_id, cluster_events)
            self.cluster_repo.save(cluster)

            # Update events with cluster ID
            for event in cluster_events:
                event.cluster_id = cluster_id
            self.event_repo.save_many(cluster_events)

            num_clusters += 1

        return {"clusters": num_clusters, "noise": noise_count}

    def get_all_clusters(self) -> list:
        """Get all clusters."""
        return self.cluster_repo.get_all()


class TimelineService:
    """Service for generating contextual timelines."""

    def __init__(self, event_repo: EventRepository):
        """Initialize timeline service."""
        self.event_repo = event_repo

    def get_timeline(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        days: Optional[int] = None,
    ) -> list[Event]:
        """Get timeline of events."""
        if days:
            end = datetime.now()
            start = end - timedelta(days=days)
        elif not start or not end:
            # Default: last 7 days
            end = datetime.now()
            start = end - timedelta(days=7)

        return self.event_repo.get_by_time_range(start, end)


class StatsService:
    """Service for generating statistics."""

    def __init__(
        self,
        event_repo: EventRepository,
        cluster_repo: ClusterRepository,
    ):
        """Initialize stats service."""
        self.event_repo = event_repo
        self.cluster_repo = cluster_repo

    def get_stats(self) -> dict:
        """Get overall statistics."""
        all_events = self.event_repo.get_all()
        all_clusters = self.cluster_repo.get_all()

        browser_events = [e for e in all_events if e.type == EventType.BROWSER]
        command_events = [e for e in all_events if e.type == EventType.COMMAND]
        commit_events = [e for e in all_events if e.type == EventType.COMMIT]

        return {
            "total_events": len(all_events),
            "browser_events": len(browser_events),
            "command_events": len(command_events),
            "commit_events": len(commit_events),
            "total_clusters": len(all_clusters),
            "clustered_events": sum(e.cluster_id is not None for e in all_events),
        }
