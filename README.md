# LinkNower

> Local-first personal workflow intelligence engine for developers

LinkNower helps you rediscover your browsing history, command-line activities, and git commits through semantic search and intelligent clustering. It's like having a photographic memory of your development workflow—completely private and running locally on your machine.

## ✨ Features

- 🔍 **Semantic Search**: Find browsing history and commands by meaning, not just keywords
- 🧩 **Activity Clustering**: Automatically group related work sessions by context
- 📅 **Contextual Timeline**: Reconstruct your workflow with browsing, commands, and commits side-by-side
- 🖥️ **Dual Interface**: Use CLI for quick queries or Web UI for visual exploration
- 🔐 **Privacy-First**: All data stays on your machine—no cloud, no tracking
- ⚡ **Batch Processing**: Efficient background indexing that doesn't slow you down
- 🎯 **Developer-Focused**: Zen browser + zsh shell + git repositories = complete context

## 🚀 Quick Start

### Installation

**Requirements**: Python 3.10 or higher

```bash
# Install via pip
pip install linknower

# Or via pipx (recommended for CLI tools)
pipx install linknower
```

### Basic Usage

**Command Line Interface:**
```bash
# Initialize LinkNower (one-time setup)
lk init

# Run your first sync (indexes all available data)
lk sync --full

# Search your history semantically
lk search "react authentication tutorial"

# View your contextual timeline
lk timeline --days 7

# Discover activity clusters
lk cluster list
```

**Web Interface:**
```bash
# Launch the Streamlit UI
streamlit run src/linknower/ui/app.py

# Or use the convenience script
./launch_ui.sh
```

The web interface provides:
- 🔍 Interactive semantic search with filters
- 📅 Visual timeline with activity charts
- 🧩 Cluster visualization and exploration
- 📊 Real-time statistics dashboard

### Example Workflow

```bash
# Find when you worked on a specific feature
lk search "database migration" --limit 10

# See what you were doing last Monday
lk timeline --date 2024-01-15

# Check cluster details for a work session
lk cluster show <cluster-id>

# Get statistics about your data
lk stats
```

## 📚 Documentation

- **[Project Overview](SPEC.md)**: Executive summary and MVP goals
- **[Documentation Index](DOCS_INDEX.md)**: Complete guide to all documentation
- **[Functional Specification](FUNCTIONAL_SPEC.md)**: Detailed requirements and acceptance criteria
- **[Architecture](ARCHITECTURE.md)**: System design and module structure
- **[Design](DESIGN.md)**: Implementation-ready technical specifications

## 🛠️ Configuration

LinkNower works out-of-the-box with sensible defaults, but you can customize:

```bash
# Edit configuration
lk config edit

# View current configuration
lk config show

# Add a git repository to monitor
lk config add-repo ~/projects/myapp
```

**Default Data Sources**:
- Zen Browser: `~/Library/Application Support/Zen/Profiles/<profile>/places.sqlite` (macOS)
- Zsh History: `~/.zsh_history`
- Git Repositories: Configured via `lk config add-repo`

**Privacy Filtering**: Sensitive patterns (passwords, API keys, tokens) are automatically excluded. Configure additional filters in your config file.

## 🧠 How It Works

LinkNower uses modern ML techniques to understand your workflow:

1. **Data Ingestion**: Reads from Zen browser SQLite, zsh history, and git logs
2. **Embedding Generation**: Converts URLs, titles, commands, and commits into semantic vectors using `sentence-transformers`
3. **Clustering**: Groups similar activities using UMAP dimensionality reduction + HDBSCAN density-based clustering
4. **Search & Query**: Performs semantic similarity search via ChromaDB vector database

All processing happens locally—no data ever leaves your machine.

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Setting up the development environment
- Code style and testing requirements
- How to submit pull requests

## 📜 License

[MIT License](LICENSE) - see LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [ChromaDB](https://www.trychroma.com/) - Local vector database
- [sentence-transformers](https://www.sbert.net/) - Semantic embeddings
- [HDBSCAN](https://hdbscan.readthedocs.io/) - Density-based clustering
- [Typer](https://typer.tiangolo.com/) - Modern CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output

---

**Status**: MVP Development | **Version**: 0.2.0 | **Last Updated**: 2024
