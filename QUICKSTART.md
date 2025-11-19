# 🚀 Quick Start Guide

Get LinkNower up and running in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Zen Browser installed
- macOS (Linux support coming soon)

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Navigate to project directory
cd /Users/harikishore/sources/2025/linknower

# Run setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install package
pip install -e .
```

## Interface Options

LinkNower provides two interfaces:

### 🖥️ Web UI (Recommended for Visual Exploration)

```bash
# Launch Streamlit interface
./launch_ui.sh

# Or manually:
streamlit run src/linknower/ui/app.py
```

**Features:**
- Interactive semantic search with live results
- Visual timeline with activity charts
- Cluster visualization and exploration
- Real-time statistics dashboard
- Filter and sort capabilities

### ⌨️ Command Line (Fast for Quick Queries)

```bash
# Search
lk search "python tutorial"

# Timeline
lk timeline --days 7

# Clusters
lk cluster
```

## First Steps

### 1. Initialize Configuration

```bash
lk init
```

This creates `~/.linknower/config.yaml` with default settings.

### 2. Add Git Repositories (Optional)

```bash
lk config --add-repo ~/projects/myapp
lk config --add-repo ~/projects/another-app
```

### 3. Sync Your Data

```bash
lk sync --full
```

This will:
- Read your Zen browser history
- Parse your zsh command history
- Extract git commits from configured repos
- Generate semantic embeddings
- Store everything locally

**First sync may take 2-5 minutes depending on data volume.**

### 4. Try Searching

```bash
# Search across all activities
lk search "react authentication"

# Search only browser history
lk search "python tutorial" --type browser

# Search only commands
lk search "git commit" --type command
```

### 5. View Your Timeline

```bash
# Last 7 days (default)
lk timeline

# Last 30 days
lk timeline --days 30

# Specific date
lk timeline --date 2025-11-15
```

### 6. Discover Activity Clusters

```bash
lk cluster
```

This analyzes your workflow and groups related activities.

### 7. Check Statistics

```bash
lk stats
```

See how much data you've indexed.

## Daily Usage

### Morning Routine
```bash
# Sync yesterday's activities
lk sync

# Review what you worked on
lk timeline --days 1

# Check for any new clusters
lk cluster
```

### During Work
```bash
# Find that tutorial you read last week
lk search "docker compose tutorial"

# Remember what you were working on yesterday
lk timeline --date 2025-11-17

# Find that git command you used
lk search "git rebase" --type command
```

### End of Week
```bash
# Review the week
lk timeline --days 7

# See your activity patterns
lk cluster

# Check your stats
lk stats
```

## Configuration

### View Current Config
```bash
lk config --show
```

### Edit Config File
```bash
# Edit manually
nano ~/.linknower/config.yaml

# Or use your editor
code ~/.linknower/config.yaml
```

### Example Configuration

```yaml
# Browser profile (supports wildcards)
zen_profile_path: "~/Library/Application Support/Zen/Profiles/*.default-release"

# Shell history
zsh_history_path: "~/.zsh_history"

# Git repositories to monitor
git_repos:
  - ~/projects/app1
  - ~/projects/app2

# ML settings
embedding_model: "all-MiniLM-L6-v2"
min_cluster_size: 5

# Privacy patterns (regex)
privacy_patterns:
  - "password\\s*=\\s*['\"]?[\\w]+['\"]?"
  - "api[_-]?key\\s*=\\s*['\"]?[\\w]+['\"]?"
```

## Troubleshooting

### "Browser database not found"
- Ensure Zen Browser is installed
- Check profile path: `ls ~/Library/Application\ Support/Zen/Profiles/`
- Update config with correct profile path

### "History file not found"
- Check if you use zsh: `echo $SHELL`
- Verify history file exists: `ls -la ~/.zsh_history`

### "Import errors"
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -e .`

### "Python version too old"
```bash
# Check version
python3 --version

# Install newer version (macOS)
brew install python@3.10

# Create venv with specific version
python3.10 -m venv venv
```

### Database locked
- Close Zen Browser before syncing
- LinkNower uses read-only mode by default

## Performance Tips

1. **First Sync**: May take several minutes for large histories
2. **Regular Syncs**: Incremental (future feature), fast
3. **Clustering**: CPU-intensive, run periodically not every sync
4. **Privacy Filter**: Adds minimal overhead

## Data Storage

All data is stored locally in `~/.linknower/`:

```
~/.linknower/
├── config.yaml          # Your configuration
├── raw.db              # Event database (SQLite)
├── clusters.db         # Cluster metadata (SQLite)
└── chroma/             # Embeddings (ChromaDB)
```

**Total storage**: ~10-100 MB depending on history size

## Privacy & Security

- ✅ All data stays local (no cloud, no telemetry)
- ✅ Sensitive patterns filtered automatically
- ✅ Read-only access to browser database
- ✅ No network requests except for downloading ML models (one-time)

## Next Steps

- Read [README.md](README.md) for detailed features
- See [DEVELOPMENT.md](DEVELOPMENT.md) for contributing
- Check [DOCS_INDEX.md](DOCS_INDEX.md) for all documentation

## Getting Help

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (coming soon)
2. Review [FAQ.md](FAQ.md) (coming soon)
3. Read the documentation: [DOCS_INDEX.md](DOCS_INDEX.md)
4. Open an issue on GitHub

---

**Happy Searching! 🔍**
