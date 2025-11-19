# Low-Level Design: LinkNower

**Version:** 1.0.0  
**Date:** November 18, 2025  
**Status:** Implementation Ready

---

## 1. Overview

This document provides implementation-ready specifications for all modules in LinkNower, including detailed class signatures, algorithms, data structures, and test scenarios.

**Reference Documents:**
- `SPEC.md`: High-level requirements
- `FUNCTIONAL_SPEC.md`: Detailed functional requirements
- `ARCHITECTURE.md`: System architecture and modular design
- `TECH.md`: Technical implementation guide

---

## 2. Module Index

| Module | File Path | Responsibilities |
|--------|-----------|------------------|
| Event Model | `domain/models/event.py` | Core event entity |
| Cluster Model | `domain/models/cluster.py` | Cluster entity and assignments |
| Embedding Model | `domain/models/embedding.py` | Embedding value object |
| Browser Parser | `domain/parsers/browser.py` | Parse Zen browser history |
| Shell Parser | `domain/parsers/shell.py` | Parse zsh history with CWD |
| Git Parser | `domain/parsers/git.py` | Parse git commits |
| Privacy Filter | `domain/filters/privacy.py` | Filter sensitive data |
| Embedding Engine | `domain/ml/embeddings.py` | Generate embeddings |
| Clustering Engine | `domain/ml/clustering.py` | UMAP + HDBSCAN clustering |
| Feature Engineer | `domain/ml/features.py` | Prepare clustering features |
| Label Generator | `domain/utils/label_generator.py` | Generate cluster labels |
| Raw Events Repo | `repositories/raw_events_repo.py` | Raw events database |
| Vector Repo | `repositories/vector_repo.py` | ChromaDB wrapper |
| Clusters Repo | `repositories/clusters_repo.py` | Clusters database |
| Sync Service | `services/sync_service.py` | Orchestrate data ingestion |
| Search Service | `services/search_service.py` | Semantic search |
| Cluster Service | `services/cluster_service.py` | Clustering workflow |
| CLI Commands | `cli/commands.py` | Typer command handlers |

**Note:** Full implementation details for all modules are provided in the comprehensive version. The key modules (parsers, models, ML components) are detailed in sections 3-6 below.

---

## 3. Key Algorithms

### 3.1 CWD Inference Algorithm

**Purpose:** Track current working directory from shell history

**Input:** Sequence of shell commands with timestamps
**Output:** CWD for each command

**Algorithm:**
```python
def infer_cwd(commands: list[str]) -> list[str]:
    current_cwd = Path.home()
    cwds = []
    
    for cmd in commands:
        parts = cmd.split()
        
        if parts and parts[0] == 'cd':
            if len(parts) == 1:
                # cd with no args → home
                current_cwd = Path.home()
            elif parts[1] == '-':
                # cd - → cannot track, keep current
                pass
            elif parts[1].startswith('/'):
                # Absolute path
                current_cwd = Path(parts[1])
            else:
                # Relative path
                current_cwd = current_cwd / parts[1]
                current_cwd = current_cwd.resolve()
        
        cwds.append(str(current_cwd))
    
    return cwds
```

**Limitations:**
- Cannot track `cd -` (previous directory)
- Cannot track `pushd/popd` stack
- Assumes history file is complete

---

### 3.2 Cluster Label Generation Algorithm

**Purpose:** Generate human-readable labels for clusters

**Input:** List of events in cluster
**Output:** Label string

**Algorithm:**
```python
def generate_cluster_label(events: list[Event]) -> str:
    """
    Generate label from cluster events.
    
    Format: "<primary_context> (<date_range>)"
    Example: "linknower (Nov 15-18)"
    """
    # 1. Find most common context (repo/cwd)
    contexts = [Path(e.context).name for e in events if e.context]
    most_common_context = Counter(contexts).most_common(1)[0][0]
    
    # 2. Get date range
    timestamps = [e.timestamp for e in events]
    start_date = datetime.fromtimestamp(min(timestamps))
    end_date = datetime.fromtimestamp(max(timestamps))
    
    start_str = start_date.strftime('%b %d')
    end_str = end_date.strftime('%b %d')
    
    if start_str == end_str:
        date_str = start_str
    else:
        date_str = f"{start_str}-{end_str}"
    
    return f"{most_common_context} ({date_str})"
```

---

### 3.3 Feature Combination Algorithm

**Purpose:** Combine temporal, semantic, and context features

**Input:**
- Events with timestamps and contexts
- Embedding vectors (384D)

**Output:** Combined feature matrix

**Algorithm:**
```python
def combine_features(
    events: list[Event],
    embeddings: np.ndarray
) -> np.ndarray:
    """
    Combine three types of features with weights.
    
    Weights: time=0.3, semantic=0.5, context=0.2
    """
    n_events = len(events)
    
    # 1. Temporal: normalize timestamps
    timestamps = np.array([e.timestamp for e in events]).reshape(-1, 1)
    scaler = StandardScaler()
    time_features = scaler.fit_transform(timestamps) * 0.3
    
    # 2. Semantic: use embeddings
    semantic_features = embeddings * 0.5
    
    # 3. Context: one-hot encoding
    contexts = [e.context for e in events]
    unique_contexts = sorted(set(contexts))
    context_map = {ctx: i for i, ctx in enumerate(unique_contexts)}
    
    context_features = np.zeros((n_events, len(unique_contexts)))
    for i, ctx in enumerate(contexts):
        context_features[i, context_map[ctx]] = 1.0
    context_features *= 0.2
    
    # 4. Combine
    combined = np.hstack([
        time_features,
        semantic_features,
        context_features
    ])
    
    return combined
```

---

## 4. Database Schemas

### 4.1 Raw Events Database (SQLite)

**File:** `~/.linknower/raw.db`

```sql
-- Core events table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('browser', 'shell', 'git')),
    content TEXT NOT NULL,
    context TEXT,
    metadata TEXT,  -- JSON
    embedding_id TEXT,
    is_sensitive BOOLEAN DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_context ON events(context);
CREATE INDEX idx_events_embedding ON events(embedding_id);

-- Ingestion tracking
CREATE TABLE ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    last_timestamp INTEGER NOT NULL,
    records_count INTEGER DEFAULT 0,
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE UNIQUE INDEX idx_ingestion_source ON ingestion_log(source);
```

---

### 4.2 Clusters Database (SQLite)

**File:** `~/.linknower/clusters.db`

```sql
-- Cluster metadata
CREATE TABLE clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    start_timestamp INTEGER NOT NULL,
    end_timestamp INTEGER NOT NULL,
    event_count INTEGER DEFAULT 0,
    primary_context TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    clustering_run_id INTEGER,
    FOREIGN KEY (clustering_run_id) REFERENCES clustering_runs(id)
);

CREATE INDEX idx_clusters_time ON clusters(start_timestamp, end_timestamp);

-- Event-to-cluster mapping
CREATE TABLE cluster_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    cluster_id INTEGER,  -- NULL for noise
    distance REAL,
    FOREIGN KEY (cluster_id) REFERENCES clusters(id)
);

CREATE INDEX idx_assignments_event ON cluster_assignments(event_id);
CREATE INDEX idx_assignments_cluster ON cluster_assignments(cluster_id);

-- Clustering run metadata
CREATE TABLE clustering_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    events_processed INTEGER,
    clusters_found INTEGER,
    noise_points INTEGER,
    parameters TEXT,  -- JSON
    duration_seconds REAL,
    metrics TEXT  -- JSON: silhouette, etc.
);
```

---

### 4.3 ChromaDB Schema

**Collection:** `linknower_events`

**Document Structure:**
```python
{
    'ids': ['browser_123', 'shell_456', 'git_789'],
    'embeddings': [[0.1, 0.2, ...], ...],  # 384D vectors
    'documents': ['Page Title domain.com', 'git commit', ...],
    'metadatas': [
        {
            'event_id': 123,
            'type': 'browser',
            'context': 'Page Title',
            'timestamp': 1700000000
        },
        ...
    ]
}
```

**Indices:** HNSW for fast similarity search (created automatically by ChromaDB)

---

## 5. API Specifications

### 5.1 Parser Interface

```python
from typing import Protocol

class Parser(Protocol):
    """Abstract parser interface."""
    
    def parse(self, since_timestamp: int) -> list[Event]:
        """
        Parse events since timestamp.
        
        Args:
            since_timestamp: Unix timestamp (seconds)
            
        Returns:
            List of Event objects
            
        Raises:
            DataSourceError: If source unavailable or corrupt
        """
        ...
    
    def is_available(self) -> bool:
        """Check if data source is accessible."""
        ...
    
    def get_latest_timestamp(self) -> int | None:
        """Get timestamp of most recent event."""
        ...
```

---

### 5.2 Repository Interfaces

#### RawEventsRepository

```python
class RawEventsRepository:
    """Repository for raw events storage."""
    
    def save(self, events: list[Event]) -> list[int]:
        """
        Save events to database.
        
        Args:
            events: List of Event objects
            
        Returns:
            List of assigned event IDs
        """
        ...
    
    def get_by_id(self, event_id: int) -> Event | None:
        """Get single event by ID."""
        ...
    
    def get_by_ids(self, event_ids: list[int]) -> list[Event]:
        """Get multiple events by IDs."""
        ...
    
    def get_since(
        self,
        timestamp: int,
        event_type: EventType | None = None
    ) -> list[Event]:
        """Get events since timestamp, optionally filtered by type."""
        ...
    
    def get_last_sync_timestamp(self, source: str) -> int | None:
        """Get last sync timestamp for source."""
        ...
    
    def update_last_sync(
        self,
        source: str,
        timestamp: int,
        records_count: int
    ) -> None:
        """Update last sync metadata."""
        ...
```

#### VectorRepository

```python
class VectorRepository:
    """Repository for vector embeddings (ChromaDB)."""
    
    def add_embeddings(
        self,
        embeddings: list[Embedding],
        events: list[Event]
    ) -> None:
        """
        Store embeddings in vector database.
        
        Args:
            embeddings: List of Embedding objects
            events: Corresponding Event objects for metadata
        """
        ...
    
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        filters: dict | None = None
    ) -> list[VectorSearchResult]:
        """
        Semantic search by vector similarity.
        
        Args:
            query_embedding: Query vector (384D)
            n_results: Number of results to return
            filters: ChromaDB where filters (e.g., {'type': 'shell'})
            
        Returns:
            List of VectorSearchResult with event_id and distance
        """
        ...
    
    def get_embeddings(self, event_ids: list[int]) -> np.ndarray:
        """
        Retrieve embeddings for given event IDs.
        
        Returns:
            Array of shape (len(event_ids), 384)
        """
        ...
```

#### ClustersRepository

```python
class ClustersRepository:
    """Repository for cluster metadata and assignments."""
    
    def save_clustering_run(
        self,
        clusters: list[Cluster],
        assignments: list[ClusterAssignment],
        metrics: ClusteringMetrics,
        parameters: dict
    ) -> int:
        """
        Save complete clustering run.
        
        Args:
            clusters: List of Cluster objects
            assignments: List of ClusterAssignment objects
            metrics: Clustering quality metrics
            parameters: Clustering parameters used
            
        Returns:
            clustering_run_id
        """
        ...
    
    def get_clusters(
        self,
        since_timestamp: int | None = None,
        limit: int | None = None
    ) -> list[Cluster]:
        """Get clusters, optionally filtered."""
        ...
    
    def get_cluster_events(self, cluster_id: int) -> list[Event]:
        """Get all events in a cluster."""
        ...
    
    def get_cluster_by_id(self, cluster_id: int) -> Cluster | None:
        """Get single cluster by ID."""
        ...
```

---

### 5.3 Service Interfaces

#### SyncService

```python
@dataclass
class SyncResult:
    """Result from sync operation."""
    source: str
    events_processed: int
    events_filtered: int
    embeddings_generated: int
    duration_seconds: float
    errors: list[str]
    
    @property
    def success(self) -> bool:
        return len(self.errors) == 0

class SyncService:
    """Orchestrate data ingestion workflow."""
    
    def sync_all(self, full_sync: bool = False) -> list[SyncResult]:
        """
        Sync all enabled sources.
        
        Args:
            full_sync: If True, ignore last sync timestamp
            
        Returns:
            List of SyncResult for each source
        """
        ...
    
    def sync_source(
        self,
        source: str,
        full_sync: bool = False
    ) -> SyncResult:
        """Sync single source."""
        ...
```

#### SearchService

```python
@dataclass
class SearchResult:
    """Single search result."""
    event: Event
    score: float  # Similarity score (0-1)
    rank: int

class SearchService:
    """Execute semantic search queries."""
    
    def search(
        self,
        query: str,
        limit: int = 10,
        event_type: EventType | None = None,
        since_days: int | None = None,
        cluster_id: int | None = None
    ) -> list[SearchResult]:
        """
        Semantic search across history.
        
        Args:
            query: Natural language search query
            limit: Maximum results to return
            event_type: Filter by event type
            since_days: Only search last N days
            cluster_id: Only search within specific cluster
            
        Returns:
            List of SearchResult, sorted by score descending
        """
        ...
```

#### ClusterService

```python
@dataclass
class ClusteringResult:
    """Result from clustering operation."""
    clusters_found: int
    noise_points: int
    events_processed: int
    duration_seconds: float
    metrics: ClusteringMetrics

class ClusterService:
    """Execute clustering workflow."""
    
    def cluster(
        self,
        window_days: int = 90,
        min_cluster_size: int = 5
    ) -> ClusteringResult:
        """
        Run clustering on recent events.
        
        Algorithm:
        1. Load events from window
        2. Load embeddings
        3. Prepare combined features
        4. Run UMAP + HDBSCAN
        5. Generate cluster labels
        6. Save results
        
        Args:
            window_days: Number of days to cluster
            min_cluster_size: Minimum events per cluster
            
        Returns:
            ClusteringResult with statistics
        """
        ...
```

---

## 6. Error Handling

### Exception Hierarchy

```python
class LinkNowerError(Exception):
    """Base exception for all LinkNower errors."""
    pass

class ConfigurationError(LinkNowerError):
    """Configuration-related errors."""
    pass

class DataSourceError(LinkNowerError):
    """Parser/ingestion errors."""
    pass

class StorageError(LinkNowerError):
    """Database/storage errors."""
    pass

class MLError(LinkNowerError):
    """ML operation errors."""
    pass

class ValidationError(LinkNowerError):
    """Input validation errors."""
    pass
```

### Error Handling Strategy

**By Layer:**

1. **Infrastructure:** Catch low-level exceptions, wrap in domain exceptions
   ```python
   try:
       conn = sqlite3.connect(db_path)
   except sqlite3.Error as e:
       raise StorageError(f"Database connection failed: {e}")
   ```

2. **Repository:** Propagate domain exceptions, add context
   ```python
   try:
       return self._query_events(since)
   except StorageError as e:
       logger.error(f"Failed to query events: {e}")
       raise
   ```

3. **Domain:** Raise specific domain exceptions
   ```python
   if not self.is_available():
       raise DataSourceError("Browser database not found")
   ```

4. **Service:** Catch domain exceptions, partial success handling
   ```python
   results = []
   for source in sources:
       try:
           result = self.sync_source(source)
           results.append(result)
       except DataSourceError as e:
           logger.error(f"Source {source} failed: {e}")
           results.append(SyncResult(source, 0, 0, 0, 0, [str(e)]))
   return results
   ```

5. **CLI:** Catch all exceptions, format user-friendly messages
   ```python
   try:
       result = sync_service.sync_all()
       console.print("[green]✓ Sync complete[/green]")
   except ConfigurationError as e:
       console.print(f"[red]Configuration error: {e}[/red]")
       sys.exit(1)
   except Exception as e:
       logger.exception("Unexpected error")
       console.print(f"[red]Unexpected error. Check logs.[/red]")
       sys.exit(3)
   ```

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Coverage Target:** >80% for all modules

**Key Test Suites:**

```python
# tests/unit/test_event_model.py
def test_event_creation():
    """Test Event object creation."""
    event = Event(
        timestamp=1700000000,
        type=EventType.BROWSER,
        content="https://example.com",
        context="Example Page"
    )
    assert event.timestamp == 1700000000
    assert event.type == EventType.BROWSER

def test_event_validation():
    """Test Event validation."""
    with pytest.raises(ValueError):
        Event(timestamp=-1, type=EventType.BROWSER, content="", context="")

# tests/unit/test_privacy_filter.py
def test_filters_password_command():
    """Test filtering of password in command."""
    filter = PrivacyFilter()
    event = Event(
        timestamp=1700000000,
        type=EventType.SHELL,
        content="export PASSWORD=secret123",
        context="/home/user"
    )
    assert filter.is_sensitive(event) == True

def test_filters_banking_url():
    """Test filtering of banking URLs."""
    filter = PrivacyFilter()
    event = Event(
        timestamp=1700000000,
        type=EventType.BROWSER,
        content="https://www.bankofamerica.com/login",
        context="Bank Login"
    )
    assert filter.is_sensitive(event) == True

# tests/unit/test_cwd_tracker.py
def test_cwd_tracking_absolute():
    """Test CWD tracking with absolute paths."""
    tracker = CWDTracker()
    assert tracker.process_command("cd /usr/local") == "/usr/local"
    assert tracker.process_command("ls -la") == "/usr/local"
    assert tracker.process_command("cd /home/user") == "/home/user"

def test_cwd_tracking_relative():
    """Test CWD tracking with relative paths."""
    tracker = CWDTracker()
    tracker.current_cwd = "/home/user"
    assert "/home/user/projects" in tracker.process_command("cd projects")
```

---

### 7.2 Integration Tests

```python
# tests/integration/test_sync_workflow.py
def test_full_sync_workflow(temp_db, test_browser_db, test_zsh_history):
    """Test complete sync workflow."""
    # Setup
    config = Config(...)
    parser = ZenBrowserParser(profile_path=test_browser_db)
    raw_repo = RawEventsRepository(temp_db)
    vector_repo = VectorRepository(...)
    embedding_engine = EmbeddingEngine()
    privacy_filter = PrivacyFilter()
    
    sync_service = SyncService(
        parsers={'browser': parser},
        privacy_filter=privacy_filter,
        embedding_engine=embedding_engine,
        raw_repo=raw_repo,
        vector_repo=vector_repo
    )
    
    # Execute
    results = sync_service.sync_all()
    
    # Assert
    assert len(results) == 1
    assert results[0].success
    assert results[0].events_processed > 0
    
    # Verify storage
    events = raw_repo.get_since(0)
    assert len(events) == results[0].events_processed

# tests/integration/test_search_workflow.py
def test_search_workflow(populated_db):
    """Test semantic search workflow."""
    # Setup
    search_service = SearchService(...)
    
    # Execute
    results = search_service.search("docker errors", limit=5)
    
    # Assert
    assert len(results) <= 5
    assert all(r.score >= 0 and r.score <= 1 for r in results)
    assert results[0].score >= results[-1].score  # Sorted by score
```

---

### 7.3 Test Fixtures

```python
# tests/fixtures/browser_history.py
@pytest.fixture
def test_browser_db(tmp_path):
    """Create test browser database."""
    db_path = tmp_path / "places.sqlite"
    conn = sqlite3.connect(db_path)
    
    # Create schema
    conn.execute("""
        CREATE TABLE moz_places (
            id INTEGER PRIMARY KEY,
            url TEXT,
            title TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE moz_historyvisits (
            id INTEGER PRIMARY KEY,
            place_id INTEGER,
            visit_date INTEGER
        )
    """)
    
    # Insert test data
    test_visits = [
        ("https://github.com", "GitHub", 1700000000 * 1_000_000),
        ("https://stackoverflow.com", "Stack Overflow", 1700000100 * 1_000_000),
    ]
    
    for i, (url, title, visit_date) in enumerate(test_visits, 1):
        conn.execute("INSERT INTO moz_places VALUES (?, ?, ?)", (i, url, title))
        conn.execute("INSERT INTO moz_historyvisits VALUES (?, ?, ?)", (i, i, visit_date))
    
    conn.commit()
    conn.close()
    
    return db_path.parent

# tests/fixtures/shell_history.py
@pytest.fixture
def test_zsh_history(tmp_path):
    """Create test zsh history file."""
    history_path = tmp_path / ".zsh_history"
    
    commands = [
        ": 1700000000:0;cd /home/user/projects",
        ": 1700000100:0;git status",
        ": 1700000200:0;docker ps",
    ]
    
    history_path.write_text('\n'.join(commands))
    
    return history_path
```

---

## 8. Performance Optimization

### 8.1 Database Optimization

**Indices:**
```sql
-- Critical indices for query performance
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_context ON events(context);

-- Composite index for common queries
CREATE INDEX idx_events_type_timestamp ON events(type, timestamp);
```

**Query Optimization:**
```python
# Use prepared statements
cursor.execute(
    "SELECT * FROM events WHERE timestamp > ? AND type = ?",
    (since_timestamp, event_type.value)
)

# Use transactions for bulk operations
with conn:
    conn.executemany(
        "INSERT INTO events VALUES (?, ?, ?, ?)",
        event_tuples
    )
```

**Vacuum Strategy:**
```python
# Periodically vacuum to reclaim space
def maintenance():
    conn.execute("VACUUM")
    conn.execute("ANALYZE")
```

---

### 8.2 Embedding Optimization

**Batch Processing:**
```python
# Process in batches for memory efficiency
BATCH_SIZE = 32

for i in range(0, len(texts), BATCH_SIZE):
    batch = texts[i:i + BATCH_SIZE]
    embeddings = model.encode(batch, batch_size=BATCH_SIZE)
    yield embeddings
```

**Model Caching:**
```python
# Singleton pattern for model
_model_cache = None

def get_embedding_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = SentenceTransformer("all-MiniLM-L6-v2")
    return _model_cache
```

---

### 8.3 Clustering Optimization

**Dimensionality Reduction First:**
```python
# Reduce to 5D before clustering (much faster)
reduced = UMAP(n_components=5).fit_transform(features)
labels = HDBSCAN().fit_predict(reduced)

# NOT: labels = HDBSCAN().fit_predict(features)  # Too slow
```

**Limit Window Size:**
```python
# Don't cluster all history, just recent window
def cluster(window_days=90):
    cutoff = time.time() - (window_days * 86400)
    events = get_events_since(cutoff)
    # ... cluster ...
```

---

## 9. Configuration Reference

### Configuration Schema

```yaml
# ~/.linknower/config.yaml

# Data sources
sources:
  browser:
    enabled: true
    type: zen  # Only 'zen' supported in MVP
    # profile_path: custom/path  # Optional override
  
  shell:
    enabled: true
    type: zsh  # Only 'zsh' supported in MVP
    # history_path: custom/path  # Optional override
  
  git:
    enabled: true
    search_paths:
      - ~/sources
      - ~/projects
      - ~/work
    max_depth: 3  # Maximum directory depth to search

# Privacy filters
privacy:
  sensitive_domains:
    - bankofamerica.com
    - chase.com
    - paypal.com
  sensitive_patterns:
    - password
    - token
    - api_key
    - secret

# Clustering configuration
clustering:
  history_window_days: 90
  min_cluster_size: 5
  min_samples: 3
  umap_n_components: 5
  umap_n_neighbors: 15

# Search configuration
search:
  default_limit: 10
  max_limit: 100

# Embeddings
embeddings:
  model: "all-MiniLM-L6-v2"
  batch_size: 32

# Logging
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: ~/.linknower/logs/linknower.log
  rotation: daily
  retention_days: 7
```

---

## 10. Deployment Checklist

### Installation

- [ ] Python ≥3.10 installed
- [ ] `pip install linknower` or `pipx install linknower`
- [ ] Run `lk init` to initialize
- [ ] Configure git search paths in config
- [ ] Run `lk sync --full` for initial ingestion
- [ ] Run `lk cluster` to generate initial clusters

### Verification

- [ ] `lk search "test"` returns results
- [ ] `lk timeline` shows clusters
- [ ] Config file exists at `~/.linknower/config.yaml`
- [ ] Databases exist in `~/.linknower/`
- [ ] No sensitive data in databases (spot check)

### Maintenance

- [ ] Run `lk sync` daily (or set up cron/launchd)
- [ ] Run `lk cluster` weekly
- [ ] Check logs periodically: `~/.linknower/logs/`
- [ ] Monitor disk usage: `du -sh ~/.linknower/`

---

## Document Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-11-18 | Initial low-level design | System |
