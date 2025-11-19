# System Architecture: LinkNower

**Version:** 1.0.0  
**Date:** November 18, 2025  
**Status:** Approved for Implementation

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────┐
│                      External Systems                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Zen Browser  │  │  Zsh Shell   │  │     Git      │     │
│  │  (SQLite)    │  │ (.zsh_hist)  │  │ (repos)      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                            │
          ╔═════════════════╧═════════════════╗
          ║        LinkNower System           ║
          ║   (Local Python Application)      ║
          ╚═══════════════════════════════════╝
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
    ┌─────▼──────┐                    ┌──────▼─────┐
    │   Storage  │                    │    CLI     │
    │ (~/.link)  │                    │  (User)    │
    └────────────┘                    └────────────┘
```

**Key Characteristics:**
- **Deployment:** Single-user, local desktop application
- **Platform:** macOS initially (Linux future)
- **Runtime:** Python ≥3.10
- **Data Flow:** Read-only from external systems, write to local storage
- **Execution Model:** Batch processing via CLI commands

---

### 1.2 Architectural Style

**Primary:** **Layered Architecture** with clear separation of concerns
**Secondary:** **Pipeline Architecture** for data processing flows

**Rationale:**
- Clear module boundaries for maintainability
- Easy to test individual layers
- Supports batch processing model
- Simple enough for solo developer maintenance

---

## 2. System Decomposition

### 2.1 Logical Layers

```
┌───────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  CLI Interface (Typer)                              │ │
│  │  - Command parsing, validation, help                │ │
│  │  - Output formatting (Rich tables, colors)          │ │
│  │  - Error handling and user feedback                 │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────┐
│                    Application Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Sync       │  │   Search     │  │  Clustering  │   │
│  │  Orchestrator│  │   Service    │  │   Service    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  - Coordinate multi-step workflows                        │
│  - Handle transactions and error recovery                 │
│  - Implement business logic                               │
└───────────────────────────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────┐
│                     Domain Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Parsers    │  │  Embeddings  │  │    Filters   │   │
│  │   (Extract)  │  │  (Transform) │  │  (Privacy)   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Clustering  │  │    Events    │  │   Clusters   │   │
│  │  (ML Logic)  │  │   (Models)   │  │   (Models)   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  - Core business logic and algorithms                     │
│  - Domain models and entities                             │
│  - Pure functions, no I/O                                 │
└───────────────────────────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────┐
│                   Data Access Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Raw DB     │  │  Embeddings  │  │  Clusters DB │   │
│  │ (SQLite Repo)│  │ (Vector Repo)│  │ (SQLite Repo)│   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  - Abstract database operations                           │
│  - Connection management                                  │
│  - Query optimization                                     │
└───────────────────────────────────────────────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   SQLite     │  │   ChromaDB   │  │   File I/O   │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐                      │
│  │   Logging    │  │    Config    │                      │
│  └──────────────┘  └──────────────┘                      │
└───────────────────────────────────────────────────────────┘
```

---

### 2.2 Module Structure

```
linknower/
├── cli/                      # Presentation Layer
│   ├── __init__.py
│   ├── commands.py          # Typer command definitions
│   ├── formatters.py        # Output formatting (Rich)
│   └── validators.py        # Input validation
│
├── services/                 # Application Layer
│   ├── __init__.py
│   ├── sync_service.py      # Orchestrates data ingestion
│   ├── search_service.py    # Semantic search coordination
│   ├── cluster_service.py   # Clustering workflow
│   └── init_service.py      # Initialization workflow
│
├── domain/                   # Domain Layer
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── event.py         # Event entity and value objects
│   │   ├── cluster.py       # Cluster entity
│   │   └── embedding.py     # Embedding value object
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract parser interface
│   │   ├── browser.py       # Zen browser parser
│   │   ├── shell.py         # Zsh history parser
│   │   └── git.py           # Git commit parser
│   │
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── privacy.py       # Sensitive data filtering
│   │   └── classifier.py    # Optional URL/command classification
│   │
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── embeddings.py    # Embedding generation
│   │   ├── clustering.py    # UMAP + HDBSCAN logic
│   │   └── features.py      # Feature engineering
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cwd_tracker.py   # CWD inference logic
│       └── label_generator.py # Cluster label generation
│
├── repositories/             # Data Access Layer
│   ├── __init__.py
│   ├── raw_events_repo.py   # Raw events database
│   ├── vector_repo.py       # ChromaDB wrapper
│   ├── clusters_repo.py     # Clusters database
│   └── config_repo.py       # Configuration storage
│
├── infrastructure/           # Infrastructure Layer
│   ├── __init__.py
│   ├── database.py          # SQLite connection management
│   ├── vector_db.py         # ChromaDB client wrapper
│   ├── logging.py           # Logging configuration
│   ├── config.py            # YAML config loader
│   └── paths.py             # Path resolution utilities
│
├── __init__.py
├── __main__.py              # Entry point
└── version.py               # Version info
```

---

## 3. Component Design

### 3.1 Presentation Layer

#### CLI Module
**Responsibility:** User interaction, command routing, output formatting

**Key Components:**
- `commands.py`: Typer command definitions
  - `init()`: Initialize system
  - `sync()`: Trigger data ingestion
  - `search()`: Semantic search
  - `timeline()`: Display clusters
  - `cluster()`: Run clustering
  - `stats()`: Show statistics

- `formatters.py`: Rich-based output formatting
  - `format_search_results()`
  - `format_timeline()`
  - `format_progress_bar()`
  - `format_error()`

- `validators.py`: Input validation
  - `validate_date_range()`
  - `validate_cluster_id()`
  - `validate_config()`

**Dependencies:** services layer, infrastructure (logging, config)

---

### 3.2 Application Layer

#### Sync Service
**Responsibility:** Orchestrate data ingestion from all sources

**Interface:**
```python
class SyncService:
    def __init__(
        self,
        parsers: dict[str, Parser],
        privacy_filter: PrivacyFilter,
        embedding_engine: EmbeddingEngine,
        raw_repo: RawEventsRepository,
        vector_repo: VectorRepository
    )
    
    def sync_all(self, full_sync: bool = False) -> SyncResult
    def sync_source(self, source: str, full_sync: bool = False) -> SyncResult
```

**Workflow:**
1. Determine sync mode (full vs incremental)
2. For each enabled source:
   - Get last sync timestamp
   - Parse new events
   - Apply privacy filters
   - Store raw events
   - Generate embeddings
   - Store embeddings
   - Update sync timestamp
3. Return aggregated results

**Error Handling:** Continue on source failure, report all errors at end

---

#### Search Service
**Responsibility:** Execute semantic search queries

**Interface:**
```python
class SearchService:
    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        vector_repo: VectorRepository,
        raw_repo: RawEventsRepository
    )
    
    def search(
        self,
        query: str,
        limit: int = 10,
        filters: SearchFilters | None = None
    ) -> list[SearchResult]
```

**Workflow:**
1. Validate query and filters
2. Embed query text
3. Query vector database with filters
4. Fetch full event details
5. Rank and return results

---

#### Cluster Service
**Responsibility:** Execute clustering workflow

**Interface:**
```python
class ClusterService:
    def __init__(
        self,
        clustering_engine: ClusteringEngine,
        raw_repo: RawEventsRepository,
        vector_repo: VectorRepository,
        clusters_repo: ClustersRepository
    )
    
    def cluster(
        self,
        window_days: int = 90,
        min_cluster_size: int = 5
    ) -> ClusteringResult
```

**Workflow:**
1. Load events from window
2. Load embeddings
3. Prepare features (time + semantic + context)
4. Run UMAP dimensionality reduction
5. Run HDBSCAN clustering
6. Generate cluster labels
7. Store cluster metadata and assignments
8. Return statistics

---

### 3.3 Domain Layer

#### Parsers Module
**Responsibility:** Extract structured data from external sources

**Interface (Abstract):**
```python
class Parser(ABC):
    @abstractmethod
    def parse(self, since_timestamp: int) -> list[Event]:
        """Parse events since given timestamp."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if source is available."""
        pass
```

**Implementations:**
- `BrowserParser`: Parses Zen Browser SQLite
- `ShellParser`: Parses .zsh_history with CWD inference
- `GitParser`: Parses git repositories

**Error Handling:** Return empty list on error, log details

---

#### Filters Module
**Responsibility:** Filter sensitive and unwanted data

**Interface:**
```python
class PrivacyFilter:
    def is_sensitive(self, event: Event) -> bool:
        """Determine if event contains sensitive data."""
        pass
    
    def should_filter(self, event: Event) -> bool:
        """Wrapper for is_sensitive (for extensibility)."""
        pass
```

**Pattern Matching:**
- Regex patterns for URLs and commands
- Domain blacklist for URLs
- Configurable user patterns

---

#### ML Module
**Responsibility:** Machine learning operations

**Components:**

1. **EmbeddingEngine**
```python
class EmbeddingEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2")
    
    def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for texts."""
        pass
    
    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query."""
        pass
```

2. **ClusteringEngine**
```python
class ClusteringEngine:
    def __init__(
        self,
        umap_n_components: int = 5,
        min_cluster_size: int = 5
    )
    
    def fit_predict(
        self,
        features: np.ndarray
    ) -> tuple[np.ndarray, ClusteringMetrics]:
        """Cluster events and return labels + metrics."""
        pass
```

3. **FeatureEngineer**
```python
class FeatureEngineer:
    def prepare_clustering_features(
        self,
        events: list[Event],
        embeddings: np.ndarray
    ) -> np.ndarray:
        """Combine time, semantic, and context features."""
        pass
```

---

#### Models Module
**Responsibility:** Domain entities and value objects

**Event Entity:**
```python
@dataclass
class Event:
    id: int | None
    timestamp: int
    type: EventType  # Enum: BROWSER, SHELL, GIT
    content: str
    context: str
    metadata: dict[str, Any]
    embedding_id: str | None = None
    is_sensitive: bool = False
```

**Cluster Entity:**
```python
@dataclass
class Cluster:
    id: int | None
    label: str
    start_timestamp: int
    end_timestamp: int
    event_count: int
    primary_context: str
    created_at: int
```

**Value Objects:** Immutable, compared by value
- `Embedding`: Wraps numpy array
- `SearchResult`: Result with score
- `SyncResult`: Aggregated sync stats

---

### 3.4 Data Access Layer

#### Repository Pattern
**Responsibility:** Abstract database operations

**Why Repository Pattern:**
- Decouples domain from database implementation
- Easy to mock for testing
- Can swap databases without changing domain logic
- Centralizes query logic

**Repositories:**

1. **RawEventsRepository**
```python
class RawEventsRepository:
    def save(self, events: list[Event]) -> None
    def get_by_id(self, event_id: int) -> Event | None
    def get_since(self, timestamp: int, type: EventType | None) -> list[Event]
    def get_last_sync_timestamp(self, source: str) -> int | None
    def update_last_sync(self, source: str, timestamp: int) -> None
```

2. **VectorRepository**
```python
class VectorRepository:
    def add_embeddings(
        self,
        embeddings: list[Embedding],
        metadatas: list[dict]
    ) -> None
    
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int,
        filters: dict | None
    ) -> list[VectorSearchResult]
    
    def get_embeddings(self, event_ids: list[int]) -> np.ndarray
```

3. **ClustersRepository**
```python
class ClustersRepository:
    def save_clusters(self, clusters: list[Cluster]) -> None
    def save_assignments(self, assignments: list[ClusterAssignment]) -> None
    def get_clusters(
        self,
        since: int | None,
        limit: int | None
    ) -> list[Cluster]
    def get_cluster_events(self, cluster_id: int) -> list[Event]
```

---

### 3.5 Infrastructure Layer

#### Database Management
```python
class DatabaseManager:
    def __init__(self, db_path: Path)
    def get_connection(self) -> sqlite3.Connection
    def execute_script(self, script: str) -> None
    def close(self) -> None
```

#### ChromaDB Client
```python
class ChromaDBClient:
    def __init__(self, persist_directory: Path)
    def get_or_create_collection(self, name: str) -> Collection
    def close(self) -> None
```

#### Configuration
```python
class Config:
    @classmethod
    def load(cls, config_path: Path) -> Config
    
    def save(self) -> None
    
    # Properties for each config section
    @property
    def sources(self) -> SourcesConfig
    
    @property
    def privacy(self) -> PrivacyConfig
    
    @property
    def clustering(self) -> ClusteringConfig
```

---

## 4. Data Flow

### 4.1 Sync Flow

```
User: lk sync
     │
     ▼
┌─────────────────┐
│ CLI Command     │
│ (sync)          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SyncService     │
│ .sync_all()     │
└────────┬────────┘
         │
         ├──────────────────────────────┬──────────────────────────────┐
         ▼                              ▼                              ▼
  ┌────────────┐                ┌────────────┐                ┌────────────┐
  │Browser     │                │Shell       │                │Git         │
  │Parser      │                │Parser      │                │Parser      │
  └─────┬──────┘                └─────┬──────┘                └─────┬──────┘
        │                             │                             │
        └──────────────────┬──────────┴──────────────────┬──────────┘
                           ▼                              │
                    ┌─────────────┐                       │
                    │ Privacy     │                       │
                    │ Filter      │                       │
                    └──────┬──────┘                       │
                           │                              │
                           ▼                              │
                    ┌─────────────┐                       │
                    │ RawEvents   │                       │
                    │ Repository  │                       │
                    └──────┬──────┘                       │
                           │                              │
                           └──────────────┬───────────────┘
                                          ▼
                                   ┌─────────────┐
                                   │ Embedding   │
                                   │ Engine      │
                                   └──────┬──────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │ Vector      │
                                   │ Repository  │
                                   └─────────────┘
```

### 4.2 Search Flow

```
User: lk search "docker errors"
     │
     ▼
┌─────────────────┐
│ CLI Command     │
│ (search)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SearchService   │
│ .search()       │
└────────┬────────┘
         │
         ├───────────────┬──────────────────┐
         ▼               ▼                  ▼
  ┌────────────┐  ┌────────────┐   ┌────────────┐
  │Embedding   │  │Vector      │   │RawEvents   │
  │Engine      │  │Repository  │   │Repository  │
  └─────┬──────┘  └─────┬──────┘   └─────┬──────┘
        │               │                │
        └───────┬───────┘                │
                │                        │
                └────────────┬───────────┘
                             ▼
                      ┌─────────────┐
                      │ Formatter   │
                      │ (Rich)      │
                      └──────┬──────┘
                             │
                             ▼
                          User sees
                          results
```

### 4.3 Cluster Flow

```
User: lk cluster
     │
     ▼
┌─────────────────┐
│ CLI Command     │
│ (cluster)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ClusterService  │
│ .cluster()      │
└────────┬────────┘
         │
         ├──────────────────┬─────────────────┐
         ▼                  ▼                 ▼
  ┌────────────┐    ┌────────────┐   ┌────────────┐
  │RawEvents   │    │Vector      │   │Feature     │
  │Repository  │    │Repository  │   │Engineer    │
  └─────┬──────┘    └─────┬──────┘   └─────┬──────┘
        │                 │                │
        └────────┬────────┴────────────────┘
                 ▼
          ┌─────────────┐
          │ Clustering  │
          │ Engine      │
          │ (UMAP+HDB)  │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │ Label       │
          │ Generator   │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │ Clusters    │
          │ Repository  │
          └─────────────┘
```

---

## 5. Cross-Cutting Concerns

### 5.1 Error Handling Strategy

**Levels:**
1. **Infrastructure:** Catch, log, wrap in domain exception
2. **Repository:** Propagate domain exceptions
3. **Domain:** Raise domain-specific exceptions
4. **Service:** Catch, aggregate, partial success handling
5. **CLI:** Catch all, format user-friendly message

**Exception Hierarchy:**
```python
class LinkNowerError(Exception):
    """Base exception"""
    pass

class ConfigurationError(LinkNowerError):
    """Config-related errors"""
    pass

class DataSourceError(LinkNowerError):
    """Parser/ingestion errors"""
    pass

class StorageError(LinkNowerError):
    """Database errors"""
    pass

class MLError(LinkNowerError):
    """ML operation errors"""
    pass
```

---

### 5.2 Logging Strategy

**Levels:**
- DEBUG: Detailed traces for development
- INFO: Normal operations (sync started, completed)
- WARNING: Recoverable issues (partial failures)
- ERROR: Operation failures requiring attention
- CRITICAL: System-level failures

**Structured Logging:**
```python
logger.info(
    "sync_completed",
    extra={
        "source": "browser",
        "events_processed": 127,
        "duration_ms": 1234,
        "timestamp": time.time()
    }
)
```

**Log File:** `~/.linknower/logs/linknower.log`
- Rotation: Daily, keep 7 days
- Format: JSON for parsing, human-readable for tail

---

### 5.3 Configuration Management

**Config Sources (Priority Order):**
1. Environment variables (e.g., `LINKNOWER_LOG_LEVEL`)
2. Config file (`~/.linknower/config.yaml`)
3. Built-in defaults

**Config Validation:**
- Schema validation on load (pydantic)
- Type checking for all values
- Clear error messages for invalid config

**Config Reloading:**
- Automatic on each command (no daemon mode)
- No hot reload needed

---

### 5.4 Testing Strategy

**Unit Tests:** 80%+ coverage
- All domain logic
- Parsers (with fixtures)
- Filters
- Feature engineering
- Label generation

**Integration Tests:**
- Repository + SQLite
- Repository + ChromaDB
- Service + repositories
- End-to-end CLI commands

**Test Fixtures:**
- Synthetic browser history
- Synthetic shell history
- Synthetic git repos
- Known-good embeddings

**Mocking:**
- Mock external systems (browsers, shell) in unit tests
- Use real databases in integration tests (in-memory SQLite)

---

### 5.5 Dependency Injection

**Strategy:** Constructor injection for testability

**Example:**
```python
# Service depends on abstractions, not implementations
class SyncService:
    def __init__(
        self,
        parsers: dict[str, Parser],  # Abstract
        privacy_filter: PrivacyFilter,
        embedding_engine: EmbeddingEngine,
        raw_repo: RawEventsRepository,  # Abstract
        vector_repo: VectorRepository  # Abstract
    ):
        self.parsers = parsers
        self.privacy_filter = privacy_filter
        self.embedding_engine = embedding_engine
        self.raw_repo = raw_repo
        self.vector_repo = vector_repo
```

**Composition Root:** `cli/commands.py`
- Wire up dependencies in command handlers
- Use factory functions for complex initialization

---

## 6. Deployment Architecture

### 6.1 Package Structure

```
linknower/
├── pyproject.toml          # Poetry/setuptools config
├── README.md
├── LICENSE
├── docs/
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── linknower/             # Source code
    └── (as above)
```

### 6.2 Installation

**Distribution:** PyPI package
```bash
pip install linknower
# or
pipx install linknower
```

**First Run:**
```bash
lk init
```

**Dependencies:**
- Managed via Poetry
- Pinned versions for reproducibility
- ~15 direct dependencies, ~40 total

---

### 6.3 Upgrade Path

**Version Compatibility:**
- Config: Forward-compatible (ignore unknown keys)
- Database: Schema versioning, migrations
- Breaking changes: Major version bump

**Migration Strategy:**
```bash
lk migrate  # Future command
```

---

## 7. Performance Considerations

### 7.1 Bottlenecks

| Operation | Bottleneck | Mitigation |
|-----------|------------|------------|
| Embedding | CPU-bound | Batch processing, optimize batch size |
| Clustering | CPU + memory | Limit history window, UMAP compression |
| Vector search | Disk I/O | ChromaDB indices, result limit |
| SQLite queries | Disk I/O | Proper indices, prepared statements |

### 7.2 Optimization Strategies

**Embedding:**
- Batch size: 32 (balance speed vs memory)
- Use float16 if precision not critical
- Cache model in memory (singleton)

**Clustering:**
- Limit to 90 days by default
- Pre-filter noise candidates (isolated events)
- Use approximate UMAP for speed

**Database:**
- Indices on timestamp, type, context
- Use transactions for bulk operations
- Vacuum regularly to reclaim space

---

## 8. Security Considerations

### 8.1 Data Privacy

**Principles:**
- Local-first: No data leaves machine
- Sensitive filtering: Before storage
- User control: Clear, configurable filters

**Risks:**
- Accidental exposure of `.linknower/` directory
- Sensitive data in logs
- Embeddings potentially reconstructible (low risk)

**Mitigations:**
- Document that `.linknower/` is sensitive
- Sanitize logs (no raw commands/URLs)
- Consider encrypting embeddings (future)

---

### 8.2 System Security

**File Permissions:**
- `~/.linknower/` should be 700 (user-only)
- Databases: 600 (user read/write only)

**Dependencies:**
- Pin versions to avoid supply chain attacks
- Regular security audits (Dependabot)
- Minimal dependency surface

---

## 9. Extensibility Points

### 9.1 Plugin Architecture (Future)

**Potential Extension Points:**
1. **Parsers:** New browsers, shells, data sources
2. **Filters:** Custom privacy rules
3. **Classifiers:** Custom URL/command categories
4. **Formatters:** Custom output formats
5. **Exporters:** Export to different formats

**Design:**
- Abstract interfaces for each extension type
- Plugin discovery via entry points
- Configuration-driven enablement

---

### 9.2 API Layer (Future)

For future web UI or IDE integrations:
```python
class LinkNowerAPI:
    def search(query: str, filters: dict) -> list[Event]
    def get_timeline(days: int) -> list[Cluster]
    def trigger_sync() -> SyncResult
    def trigger_clustering() -> ClusteringResult
```

---

## 10. Non-Functional Requirements Mapping

| NFR | Architectural Decision |
|-----|------------------------|
| Performance | Batch processing, indexed databases, efficient algorithms |
| Scalability | Configurable windows, data retention policies |
| Maintainability | Layered architecture, DI, clear interfaces |
| Testability | Repository pattern, constructor injection |
| Usability | Rich CLI, clear error messages, sensible defaults |
| Privacy | Local-first, filtering before storage |
| Reliability | Partial failure handling, transactional operations |

---

## Appendix A: Technology Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Language | Python | ≥3.10 | ML ecosystem, developer familiarity |
| CLI | Typer | ^0.9.0 | Type-safe, modern, excellent UX |
| Output | Rich | ^13.7.0 | Beautiful formatting, colors, tables |
| Embeddings | sentence-transformers | ^2.2.0 | Pre-trained models, easy to use |
| Vector DB | ChromaDB | ^0.4.0 | Local-first, simple API |
| Clustering | HDBSCAN | ^0.8.33 | Density-based, no preset K |
| Dim. Reduction | UMAP | ^0.5.5 | Fast, preserves structure |
| Config | PyYAML | ^6.0 | Human-readable, widely used |
| Testing | pytest | ^7.4.0 | Standard, extensive plugins |
| Type Checking | mypy | ^1.5.0 | Static analysis, catch bugs early |

---

## Appendix B: Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| Repository | Data Access | Abstract database operations |
| Factory | Service creation | Complex object initialization |
| Strategy | Parsers | Interchangeable parsing algorithms |
| Template Method | Base Parser | Common parsing flow, specific steps |
| Dependency Injection | Throughout | Testability, flexibility |
| Builder | Config | Complex configuration objects |
| Singleton | Embedding Model | Expensive to load, shared |
| Observer | Progress bars | Async progress updates (future) |

---

## Document Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-11-18 | Initial architecture document | System |
