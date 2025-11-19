
# LinkNower - Project Overview

**Version:** 0.2.0  
**Status:** Executive Summary  
**Last Updated:** November 18, 2025

> **📖 Documentation Index:** This is a high-level overview. For detailed specifications, see:
> - **[FUNCTIONAL_SPEC.md](FUNCTIONAL_SPEC.md)** - Detailed requirements and acceptance criteria
> - **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and modular design
> - **[DESIGN.md](DESIGN.md)** - Low-level implementation details
> - **[DOCS_INDEX.md](DOCS_INDEX.md)** - Complete documentation index

---

## 1. 🎯 Project Goal

To build a **local-first personal search engine for developer workflows** that ingests browser history, shell commands, and git commits to enable powerful semantic search and automatic activity clustering. This system transforms raw history logs into an active, searchable, context-aware knowledge base.

**Core Value:** Find what you did, why you did it, and how to resume work using natural language queries.

**Design Principles:**
- Local-first: All data stays on your machine
- Batch processing: Daily/weekly clustering, not real-time
- Lean MVP: Single browser, single shell, simple interface
- Privacy-aware: Filter sensitive data before processing

---

## 2. 📥 Ingestion & Parsing

This layer is responsible for collecting, parsing, and standardizing raw data from multiple sources.

### 2.1. Browser History

* **Source:** Zen Browser SQLite history database (Firefox-based, typically at `~/Library/Application Support/Zen/Profiles/<profile>/places.sqlite` on macOS).
* **Schema:** Normalize into: `(timestamp, url, page_title)`.
* **Scope:** Focus on single browser for MVP; additional browsers can be added later.

### 2.2. Shell History

* **Source:** Parse `.zsh_history` file periodically.
* **Schema:** Normalize into: `(timestamp, raw_command, current_working_directory)`.
* **Key Requirement:** Capturing the **Current Working Directory (CWD)** is critical for distinguishing project contexts.
* **Scope:** Focus on zsh for MVP; additional shells can be added later.

### 2.3. Git Commit History

* **Source:** Parse `.git/logs/HEAD` and commit metadata from repositories in monitored directories.
* **Schema:** Normalize into: `(timestamp, commit_hash, commit_message, branch_name, repository_path, files_changed)`.
* **Key Requirement:** Integrate commit context with browser/shell activity to enrich task clusters with code change information.

---

## 3. ⚙️ Feature Engineering & Enrichment

This layer transforms raw, standardized data into features suitable for machine learning.

### 3.1. URL Classification (Optional)

* **Goal:** Categorize the *purpose* of a visited URL for filtering and display.
* **Method:** Simple regex-based domain matching.
* **Output Tags:** `[VCS]`, `[Q&A]`, `[Docs]`, `[Local_Dev]`.
* **Scope:** Keep rules minimal; primarily used as search filters, not clustering features.

### 3.2. Command Classification (Optional)

* **Goal:** Categorize the *function* of a shell command for filtering and display.
* **Method:** Parse the command's primary executable (e.g., `git`, `docker`, `npm`).
* **Output Tags:** `[Git]`, `[Docker]`, `[NPM]`, `[Kubernetes]`.
* **Scope:** Keep rules minimal; primarily used as search filters, not clustering features.

### 3.3. Semantic Embedding

* **Goal:** Create numerical vector representations of the *meaning* of an activity.
* **Method:** Use a pre-trained sentence transformer model (~100MB, e.g., `all-MiniLM-L6-v2`) to generate embeddings for:
    1.  **Browser:** `page_title` (and potentially concatenated with key URL parts).
    2.  **Shell:** `raw_command`.
    3.  **Git:** `commit_message`.
* **Storage:** All embeddings stored in local vector database for semantic search.

---

## 4. 🧠 Core ML Model: Activity Clustering

This is the primary ML function, responsible for "grouping" related events.

* **Algorithm:** Density-based clustering using **HDBSCAN**.
    * **Rationale:** Handles unknown number of clusters and identifies noise (miscellaneous activities that don't belong to specific tasks).
* **Clustering Features:** Each event (browser visit, shell command, or git commit) is a point in multi-dimensional space:
    1.  **Time (`timestamp`):** Primary dimension for temporal grouping.
    2.  **Semantic (`embedding`):** Vector embedding of title/command/message.
    3.  **Context (`repository_path` or `current_working_directory`):** Strong signal for project context.
* **Execution:** Batch processing (daily or weekly) rather than real-time. Process last 3-6 months of history.
* **Output:** Clusters representing distinct tasks, each containing associated history items.

---

## 5. 💡 User-Facing Features

This defines how the user will interact with the processed data.

### 5.1. Feature: Semantic Search (PRIMARY)

* **Description:** Natural language queries across entire workflow history.
* **Implementation:**
    1.  Store all embeddings in local **vector database** (ChromaDB or LanceDB).
    2.  Embed user's search query using the same sentence transformer model.
    3.  Perform vector similarity search to find semantically relevant items (commands, docs, commits).
    4.  Filter results by task clusters, date ranges, or optional classification tags.
* **Interface:** CLI command: `lk search "docker compose errors"` returns relevant history items.

### 5.2. Feature: Contextual Timeline

* **Description:** View clusters (tasks) as a timeline rather than raw chronological events.
* **Implementation:**
    1.  Display clusters with date ranges and activity counts.
    2.  Generate simple cluster labels using heuristics (e.g., most common repository name + date range).
    3.  Show constituent items (URLs, commands, commits) within each cluster.
* **Interface:** CLI command: `lk timeline` or `lk timeline --last 30d`.