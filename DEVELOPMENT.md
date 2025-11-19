# Development Guide

## Prerequisites

- Python 3.10 or higher
- Git
- Zen Browser (for testing browser integration)

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd linknower
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Install LinkNower in editable mode

3. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

## Project Structure

```
linknower/
├── src/linknower/          # Source code
│   ├── domain/             # Domain models (Event, Cluster, Embedding)
│   ├── data/               # Data access (parsers, repositories)
│   ├── ml/                 # ML components (embedding, clustering)
│   ├── services/           # Application services
│   ├── cli/                # CLI interface
│   └── utils/              # Utilities (config, privacy filter)
├── tests/                  # Test suite
├── docs/                   # Documentation
└── pyproject.toml          # Project configuration
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=linknower --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

## Code Quality

### Formatting
```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/
```

### Linting
```bash
# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

### Run all checks
```bash
# Format, lint, and test
black src/ tests/ && isort src/ tests/ && ruff check src/ tests/ && pytest
```

## Using the CLI

After installation, the `lk` command will be available:

```bash
# Initialize configuration
lk init

# Sync data
lk sync --full

# Search
lk search "python tutorial"

# View timeline
lk timeline --days 7

# Cluster events
lk cluster

# Show statistics
lk stats

# Manage configuration
lk config --show
lk config --add-repo ~/projects/myapp
```

## Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test:**
   ```bash
   # Edit code
   # Run tests
   pytest
   ```

3. **Format and lint:**
   ```bash
   black src/ tests/
   isort src/ tests/
   ruff check src/ tests/
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/my-feature
   ```

## Architecture Overview

LinkNower follows a layered architecture:

1. **Presentation Layer** (`cli/`): User interface via Typer CLI
2. **Application Layer** (`services/`): Business logic orchestration
3. **Domain Layer** (`domain/`): Core models and business rules
4. **Data Access Layer** (`data/`): Parsers and repositories
5. **Infrastructure Layer** (`ml/`, `utils/`): ML components and utilities

## Key Components

### Data Parsers
- `ZenBrowserParser`: Extracts browsing history from Zen Browser SQLite
- `ZshHistoryParser`: Parses zsh command history
- `GitParser`: Extracts commit history from git repositories

### Repositories
- `SQLiteEventRepository`: Persists events to SQLite
- `SQLiteClusterRepository`: Persists clusters to SQLite
- `ChromaDBEmbeddingRepository`: Manages embeddings in ChromaDB

### ML Components
- `EmbeddingEngine`: Generates semantic embeddings using sentence-transformers
- `FeatureEngineer`: Combines temporal, semantic, and contextual features
- `ClusteringEngine`: Performs UMAP + HDBSCAN clustering

### Services
- `SyncService`: Orchestrates data ingestion
- `SearchService`: Handles semantic search
- `ClusterService`: Manages clustering
- `TimelineService`: Generates timelines
- `StatsService`: Computes statistics

## Configuration

Configuration is managed via:
1. YAML file at `~/.linknower/config.yaml`
2. Environment variables (prefix: `LINKNOWER_`)
3. `.env` file

Example configuration:
```yaml
zen_profile_path: "~/Library/Application Support/Zen/Profiles/*.default-release"
zsh_history_path: "~/.zsh_history"
git_repos:
  - ~/projects/app1
  - ~/projects/app2
embedding_model: "all-MiniLM-L6-v2"
min_cluster_size: 5
privacy_patterns:
  - "password\\s*=\\s*['\"]?[\\w]+['\"]?"
  - "api[_-]?key\\s*=\\s*['\"]?[\\w]+['\"]?"
```

## Debugging

### Enable verbose logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect databases
```bash
# View raw events
sqlite3 ~/.linknower/raw.db "SELECT * FROM events LIMIT 10;"

# View clusters
sqlite3 ~/.linknower/clusters.db "SELECT * FROM clusters;"
```

## Common Issues

### Import Errors
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall package: `pip install -e .`

### Browser Database Locked
- Close Zen Browser before syncing
- Or use SQLite read-only mode (already implemented)

### Python Version Issues
- Check version: `python3 --version`
- Install Python 3.10+: `brew install python@3.10`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [HDBSCAN Documentation](https://hdbscan.readthedocs.io/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
