# Functional Specification: LinkNower

**Version:** 1.0.0  
**Date:** November 18, 2025  
**Status:** Approved for Design

---

## 1. Executive Summary

LinkNower is a local-first personal workflow intelligence engine that automatically organizes and makes searchable a developer's daily activities across browser, terminal, and git repositories. The system enables semantic search across historical activities and automatically clusters related work into discoverable tasks.

### 1.1 Key Stakeholders

- **Primary User:** Individual software developers working on multiple projects
- **Use Context:** Daily development workflow, retrospective analysis, context recovery

### 1.2 Success Metrics

- Search relevance: >80% of searches return useful results in top 5
- Cluster quality: >70% of clusters represent coherent work sessions
- Performance: Full sync + cluster completes in <15 minutes for 3-month history
- Privacy: Zero sensitive data (passwords, tokens) stored

---

## 2. Functional Requirements

### FR-1: Data Ingestion

#### FR-1.1: Browser History Ingestion
**Priority:** P0 (Must Have)

**Description:** System shall ingest browsing history from Zen Browser.

**Inputs:**
- Zen Browser SQLite database at `~/Library/Application Support/Zen/Profiles/<profile>/places.sqlite`
- Optional: Last sync timestamp to enable incremental ingestion

**Processing:**
1. Locate Zen profile directory (support multiple profiles, use default)
2. Copy SQLite database to temporary location (avoid lock conflicts)
3. Query `moz_places` and `moz_historyvisits` tables
4. Extract: timestamp (microseconds → seconds), URL, page title
5. Filter out sensitive URLs (banking, payment sites)
6. Normalize data to internal schema

**Outputs:**
- List of browser events: `(timestamp, url, page_title, metadata)`
- Ingestion statistics: records processed, filtered, errors

**Edge Cases:**
- Profile not found: Fail gracefully with clear error message
- Database locked: Retry with exponential backoff (3 attempts)
- Corrupt database: Skip and log error, continue with other sources
- Empty history: Log warning, continue processing

**Acceptance Criteria:**
- [ ] Successfully ingests 10K+ URLs from test database
- [ ] Filters out URLs matching sensitive domain patterns
- [ ] Completes ingestion of 30 days history in <30 seconds
- [ ] Handles missing profile directory gracefully

---

#### FR-1.2: Shell History Ingestion
**Priority:** P0 (Must Have)

**Description:** System shall ingest command history from zsh with working directory inference.

**Inputs:**
- Zsh history file at `~/.zsh_history`
- Optional: Last sync timestamp

**Processing:**
1. Parse extended zsh format: `: <timestamp>:<duration>;<command>`
2. Extract timestamp, command text
3. Infer current working directory by tracking `cd` commands
4. Filter out sensitive commands (containing passwords, tokens, API keys)
5. Normalize to internal schema

**Outputs:**
- List of shell events: `(timestamp, command, cwd, metadata)`
- Ingestion statistics
- CWD inference accuracy metrics (for telemetry)

**Edge Cases:**
- History file not found: Fail gracefully
- Non-extended format: Skip lines without timestamp
- `cd -` command: Keep current CWD (cannot infer previous directory)
- `pushd/popd`: Track only as CWD changes, don't maintain stack
- Symlinks: Resolve to absolute paths where possible
- Commands with newlines: Handle multi-line commands correctly

**Limitations (Documented):**
- CWD inference is best-effort; may be inaccurate if history file incomplete
- Cannot track `pushd/popd` stack or `cd -` accurately
- Recommend atuin/mcfly for future enhancement

**Acceptance Criteria:**
- [ ] Successfully parses 1000+ commands with timestamps
- [ ] Correctly infers CWD for 90%+ of simple `cd` commands
- [ ] Filters commands containing "password", "token", "api_key"
- [ ] Handles multi-line commands gracefully

---

#### FR-1.3: Git History Ingestion
**Priority:** P0 (Must Have)

**Description:** System shall ingest commit history from git repositories in configured search paths.

**Inputs:**
- List of search paths (e.g., `~/sources`, `~/projects`)
- Optional: Last sync timestamp per repository

**Processing:**
1. Recursively find all `.git` directories in search paths (max depth: configurable, default 3)
2. For each repository, run `git log` with custom format
3. Extract: timestamp, commit hash, message, branch, files changed
4. Associate with repository path for context
5. Filter sensitive commit messages (same patterns as shell)
6. Normalize to internal schema

**Outputs:**
- List of git events: `(timestamp, commit_hash, commit_message, branch, repo_path, files_changed)`
- Repository discovery log

**Edge Cases:**
- No git repositories found: Log warning, continue
- Corrupt git repository: Skip and log error
- Detached HEAD: Use "detached" as branch name
- Bare repositories: Skip (no working commits)
- Large repositories: Limit to last N commits (configurable)

**Acceptance Criteria:**
- [ ] Discovers all git repos in test directory structure
- [ ] Successfully parses commits with various formats (merge commits, etc.)
- [ ] Completes ingestion of 500 commits across 5 repos in <10 seconds
- [ ] Handles missing/corrupt repos without failing entire ingestion

---

#### FR-1.4: Incremental Ingestion
**Priority:** P1 (Should Have)

**Description:** System shall support incremental ingestion to avoid reprocessing historical data.

**Requirements:**
- Track last successful ingestion timestamp per source
- Only process events newer than last timestamp
- Handle clock skew and timezone issues
- Provide option for full re-sync

**Acceptance Criteria:**
- [ ] Subsequent syncs only process new events
- [ ] Full re-sync option available via CLI flag `--full`

---

### FR-2: Privacy & Security

#### FR-2.1: Sensitive Data Filtering
**Priority:** P0 (Must Have)

**Description:** System shall prevent storage of sensitive information.

**Sensitive Patterns:**
- URLs containing: banking domains, payment processors
- Commands containing: `password`, `token`, `api_key`, `secret`, `.env`
- Long hexadecimal strings (likely tokens): `[a-fA-F0-9]{32,}`
- Bearer tokens: `bearer [a-zA-Z0-9_-]+`

**Requirements:**
1. Apply filters BEFORE embedding generation
2. Mark filtered events in database (for audit)
3. Never store original content of filtered events
4. Support user-defined filter patterns in config

**Acceptance Criteria:**
- [ ] Filters test cases: `export API_KEY=abc123`, `https://bankofamerica.com`
- [ ] Filtered events marked but not deleted (for statistics)
- [ ] User can add custom patterns via config file
- [ ] Zero false negatives on test suite of 100 sensitive samples

---

#### FR-2.2: Local-First Architecture
**Priority:** P0 (Must Have)

**Description:** All data processing and storage shall occur locally.

**Requirements:**
- No network calls during ingestion, embedding, or clustering
- Embedding model downloaded once during initialization
- All databases stored in `~/.linknower/`
- No telemetry or usage tracking

**Acceptance Criteria:**
- [ ] System works completely offline after initial setup
- [ ] No network requests detected during normal operation
- [ ] All data files under user's home directory

---

### FR-3: Feature Engineering

#### FR-3.1: Semantic Embedding Generation
**Priority:** P0 (Must Have)

**Description:** System shall generate semantic embeddings for all non-sensitive events.

**Model:** `all-MiniLM-L6-v2` (sentence-transformers)
- Embedding dimension: 384
- Model size: ~80MB
- Inference: CPU-compatible

**Input Preparation:**
- **Browser events:** Concatenate `page_title + " " + url_domain`
- **Shell events:** Use `command` as-is
- **Git events:** Concatenate `commit_message + " " + repo_name`

**Requirements:**
1. Generate embeddings in batches (batch_size=32) for efficiency
2. Store embeddings in ChromaDB with event_id reference
3. Normalize embeddings (L2 normalization)
4. Handle empty/null text gracefully (skip or use placeholder)

**Performance:**
- Target: 1000 events/second on modern CPU
- Memory: <2GB peak usage

**Acceptance Criteria:**
- [ ] Generates embeddings for 10K events in <15 seconds
- [ ] Embeddings stored with correct dimensionality (384)
- [ ] Handles edge cases (empty strings, unicode, very long text)

---

#### FR-3.2: Optional Classification
**Priority:** P2 (Nice to Have)

**Description:** System may classify URLs and commands for filtering/display.

**URL Categories:**
- VCS: github.com, gitlab.com, bitbucket.org
- Q&A: stackoverflow.com, stackexchange.com
- Docs: /docs/, /documentation/
- Local_Dev: localhost, 127.0.0.1

**Command Categories:**
- Git: `^git `
- Docker: `^docker `, `^docker-compose `
- NPM: `^npm `, `^yarn `, `^pnpm `
- Python: `^python `, `^pip `

**Requirements:**
- Regex-based classification only (no ML)
- Store as tags in metadata JSON field
- Optional: user-defined categories in config

**Acceptance Criteria:**
- [ ] Classifies 90%+ of common URLs correctly
- [ ] Classification adds <1 second to 10K event processing

---

### FR-4: Activity Clustering

#### FR-4.1: Cluster Generation
**Priority:** P0 (Must Have)

**Description:** System shall automatically cluster related events into tasks.

**Algorithm:** UMAP + HDBSCAN
1. **Dimensionality Reduction:** UMAP (384D → 5D)
   - Metric: Euclidean
   - n_neighbors: 15
   - min_dist: 0.1

2. **Clustering:** HDBSCAN
   - min_cluster_size: 5 (configurable)
   - min_samples: 3
   - metric: Euclidean
   - cluster_selection_method: EOM (Excess of Mass)

**Feature Combination:**
- Time features (normalized timestamp): weight 0.3
- Semantic embeddings (384D): weight 0.5
- Context features (one-hot repo/cwd): weight 0.2

**Requirements:**
1. Process events from last N days (configurable, default 90)
2. Generate cluster labels using heuristics
3. Identify noise points (unclustered events)
4. Store cluster metadata and assignments

**Cluster Label Generation:**
- Format: `<repo_name> (<date_range>)`
- Example: `linknower (Nov 15-Nov 18)`
- Use most common repo/directory name in cluster
- Use date range of cluster span

**Acceptance Criteria:**
- [ ] Clusters 10K events in <5 minutes
- [ ] Generates 10-50 clusters for typical 30-day history
- [ ] Noise points <30% of total events
- [ ] Clusters visually inspected for coherence (manual QA)

---

#### FR-4.2: Cluster Quality Metrics
**Priority:** P1 (Should Have)

**Description:** System shall compute cluster quality metrics for evaluation.

**Metrics:**
1. Silhouette score (per cluster)
2. Number of clusters generated
3. Noise ratio (unclustered events / total)
4. Temporal coherence (time span of cluster)
5. Context purity (% events with same repo/cwd)

**Requirements:**
- Store metrics with each clustering run
- Display in CLI when running cluster command
- Log to file for analysis

**Acceptance Criteria:**
- [ ] Metrics computed and stored for each run
- [ ] Metrics accessible via `lk cluster --stats`

---

### FR-5: Search & Query

#### FR-5.1: Semantic Search
**Priority:** P0 (Must Have)

**Description:** Users shall search workflow history using natural language queries.

**Interface:** `lk search <query> [options]`

**Options:**
- `--limit N`: Return top N results (default: 10)
- `--type <browser|shell|git>`: Filter by event type
- `--days N`: Only search last N days
- `--cluster <id>`: Only search within specific cluster

**Processing:**
1. Embed query using same sentence transformer model
2. Perform cosine similarity search in ChromaDB
3. Apply filters (type, date, cluster)
4. Rank by similarity score
5. Fetch full event details from raw.db
6. Format and display results

**Output Format:**
```
Search Results: "docker compose errors"
─────────────────────────────────────────────────
Type    When              Content                          Score
shell   2025-11-15 14:23  docker-compose up -d --build    0.87
browser 2025-11-15 14:25  Stack Overflow: Docker Compose  0.84
shell   2025-11-15 14:30  docker-compose logs -f          0.81
```

**Acceptance Criteria:**
- [ ] Returns results in <1 second for typical query
- [ ] Relevant results in top 5 for 80%+ of test queries
- [ ] Handles typos gracefully (embeddings capture meaning)
- [ ] Empty results handled with helpful message

---

#### FR-5.2: Timeline View
**Priority:** P0 (Must Have)

**Description:** Users shall view task clusters as a timeline.

**Interface:** `lk timeline [options]`

**Options:**
- `--days N`: Show last N days (default: 30)
- `--verbose`: Show event details within clusters
- `--cluster <id>`: Show details of specific cluster

**Output Format:**
```
Task Timeline (Last 30 days)
─────────────────────────────────────────────────
Task                    Period          Events  Context
linknower (Nov 15-18)  Nov 15 - Nov 18   127    ~/sources/linknower
api-refactor (Nov 12)  Nov 12             43    ~/work/api
docker-debug (Nov 10)  Nov 10 - Nov 11    22    ~/projects/devops
```

**Verbose Mode:**
```
linknower (Nov 15-18)
  [browser] 14:23: HDBSCAN documentation - scikit-learn
  [shell]   14:25: pip install hdbscan
  [git]     14:30: Add clustering implementation
  [shell]   14:35: pytest tests/test_clustering.py
  ...
```

**Acceptance Criteria:**
- [ ] Displays clusters sorted by recency
- [ ] Verbose mode shows up to 10 events per cluster
- [ ] Renders cleanly in 80-column terminal
- [ ] Empty timeline handled with helpful message

---

#### FR-5.3: Statistics & Insights
**Priority:** P2 (Nice to Have)

**Description:** Users may view statistics about their workflow.

**Interface:** `lk stats [options]`

**Metrics:**
- Total events ingested (by type)
- Active time periods
- Top repositories/projects
- Most common commands
- Clustering statistics

**Acceptance Criteria:**
- [ ] Displays summary statistics
- [ ] Completes in <2 seconds

---

### FR-6: Configuration & Initialization

#### FR-6.1: First-Time Setup
**Priority:** P0 (Must Have)

**Description:** System shall guide user through initial setup.

**Interface:** `lk init`

**Process:**
1. Create `~/.linknower/` directory structure
2. Download embedding model (~80MB with progress bar)
3. Create default configuration file
4. Initialize databases
5. Prompt user to configure git search paths
6. Run initial sync (optional, user confirmed)

**Directory Structure Created:**
```
~/.linknower/
├── config.yaml
├── raw.db
├── embeddings/
│   └── (ChromaDB files)
├── clusters.db
└── logs/
    └── linknower.log
```

**Acceptance Criteria:**
- [ ] Completes setup without errors on fresh system
- [ ] Creates all required directories and files
- [ ] Model download shows progress
- [ ] User can skip initial sync

---

#### FR-6.2: Configuration File
**Priority:** P0 (Must Have)

**Description:** System shall support user configuration via YAML file.

**Location:** `~/.linknower/config.yaml`

**Schema:**
```yaml
sources:
  browser:
    enabled: true
    type: zen
  shell:
    enabled: true
    type: zsh
  git:
    enabled: true
    search_paths:
      - ~/sources
      - ~/projects

privacy:
  sensitive_domains:
    - bankofamerica.com
  sensitive_patterns:
    - password
    - token

clustering:
  history_window_days: 90
  min_cluster_size: 5
  schedule: weekly

search:
  default_limit: 10
```

**Acceptance Criteria:**
- [ ] Valid YAML parsed correctly
- [ ] Invalid YAML shows clear error message
- [ ] Missing keys use sensible defaults
- [ ] Changes take effect on next command

---

### FR-7: Sync & Maintenance

#### FR-7.1: Manual Sync
**Priority:** P0 (Must Have)

**Description:** Users shall manually trigger data ingestion.

**Interface:** `lk sync [options]`

**Options:**
- `--full`: Ignore last sync timestamp, re-ingest all
- `--source <browser|shell|git>`: Sync only specific source

**Process:**
1. Check last sync timestamp per source
2. Ingest new events since last sync
3. Generate embeddings for new events
4. Update ingestion log
5. Display summary statistics

**Output:**
```
Syncing workflow data...
✓ Browser: 47 new visits
✓ Shell:   123 new commands  
✓ Git:     5 new commits

Generated 175 embeddings in 2.3s
Last sync: 2025-11-18 09:15:42
```

**Acceptance Criteria:**
- [ ] Incremental sync processes only new events
- [ ] Full sync reprocesses all history
- [ ] Errors don't prevent other sources from syncing
- [ ] Summary shows what was processed

---

#### FR-7.2: Clustering Execution
**Priority:** P0 (Must Have)

**Description:** Users shall manually trigger clustering.

**Interface:** `lk cluster [options]`

**Options:**
- `--days N`: Cluster last N days (default: 90)
- `--min-size N`: Minimum cluster size (default: 5)
- `--stats`: Show quality metrics after clustering

**Process:**
1. Load events from last N days
2. Load embeddings from ChromaDB
3. Prepare combined features
4. Run UMAP + HDBSCAN
5. Generate cluster labels
6. Store results in clusters.db
7. Display summary

**Output:**
```
Clustering 8,234 events from last 90 days...
✓ Dimensionality reduction (UMAP): 12.4s
✓ Clustering (HDBSCAN): 3.7s

Found 23 task clusters
Noise points: 1,247 (15.1%)
Average cluster size: 304 events

Run 'lk timeline' to view clusters
```

**Acceptance Criteria:**
- [ ] Completes clustering in <15 minutes for 90 days
- [ ] Results viewable immediately via timeline
- [ ] Old cluster assignments overwritten
- [ ] Progress shown during long operations

---

#### FR-7.3: Scheduled Sync (Future)
**Priority:** P3 (Future Enhancement)

**Description:** System may run sync automatically via cron/launchd.

**Requirements:**
- Installation script sets up launchd plist (macOS)
- Runs daily at 2 AM
- Logs output to file
- Failures send notification (optional)

---

### FR-8: CLI User Experience

#### FR-8.1: Rich Output
**Priority:** P1 (Should Have)

**Description:** CLI shall provide rich, colored, formatted output.

**Requirements:**
- Use `rich` library for tables, progress bars, colors
- Support plain output mode for scripting (`--plain` flag)
- Respect NO_COLOR environment variable
- Handle narrow terminals gracefully (>80 columns recommended)

**Acceptance Criteria:**
- [ ] Output looks professional and readable
- [ ] Colors used semantically (red=error, green=success, etc.)
- [ ] Plain mode produces parseable output

---

#### FR-8.2: Error Handling
**Priority:** P0 (Must Have)

**Description:** CLI shall handle errors gracefully with helpful messages.

**Error Categories:**
1. **User Errors:** Invalid arguments, missing config
   - Show clear error + suggestion
   - Exit code: 1

2. **System Errors:** File not found, permission denied
   - Show error + troubleshooting steps
   - Exit code: 2

3. **Internal Errors:** Unexpected exceptions
   - Show error + request bug report with logs
   - Exit code: 3

**Example:**
```
Error: Zen profile not found

Possible solutions:
  1. Install Zen Browser
  2. Check if Zen is at: ~/Library/Application Support/Zen/
  3. Configure custom path in ~/.linknower/config.yaml

Need help? Check logs at ~/.linknower/logs/linknower.log
```

**Acceptance Criteria:**
- [ ] All errors show actionable messages
- [ ] No raw Python tracebacks shown to user
- [ ] Logs contain full debug information

---

#### FR-8.3: Help & Documentation
**Priority:** P0 (Must Have)

**Description:** CLI shall provide comprehensive help.

**Commands:**
- `lk --help`: Show all commands
- `lk <command> --help`: Show command-specific help
- `lk --version`: Show version number

**Acceptance Criteria:**
- [ ] Help text includes examples
- [ ] All options documented
- [ ] Help accessible without config/setup

---

## 3. Non-Functional Requirements

### NFR-1: Performance

| Metric | Target | Measured At |
|--------|--------|-------------|
| Initial sync (3 months) | <5 minutes | FR-7.1 |
| Incremental sync | <30 seconds | FR-7.1 |
| Embedding generation | >1000 events/sec | FR-3.1 |
| Clustering (90 days) | <15 minutes | FR-7.2 |
| Search query | <1 second | FR-5.1 |
| Timeline rendering | <2 seconds | FR-5.2 |

### NFR-2: Scalability

| Dimension | Limit | Mitigation |
|-----------|-------|------------|
| Events stored | 500K | Configurable retention period |
| Embedding DB size | <2GB | ChromaDB compression |
| Clustering window | 90 days | Configurable, older data archived |
| Git repositories | 50 | Parallel processing |

### NFR-3: Reliability

- **Data Integrity:** All database operations use transactions
- **Crash Recovery:** Partial ingestion can be resumed
- **Backup:** User responsible (all data in ~/.linknower/)
- **Logging:** All operations logged with timestamps

### NFR-4: Usability

- **Learning Curve:** User productive within 10 minutes of `lk init`
- **Documentation:** README covers 90% of use cases
- **Error Messages:** Actionable, not technical jargon
- **Defaults:** Sensible defaults work for most users

### NFR-5: Maintainability

- **Code Coverage:** >80% for core modules
- **Type Hints:** All public functions type-hinted
- **Documentation:** Docstrings for all public APIs
- **Dependencies:** Minimize external dependencies (<15 direct)

---

## 4. Out of Scope (MVP)

The following features are explicitly excluded from MVP:

1. **Multi-browser support:** Only Zen Browser
2. **Multi-shell support:** Only zsh
3. **Web UI:** CLI only
4. **Real-time clustering:** Batch only
5. **Cloud sync:** Local-first only
6. **Team features:** Single-user only
7. **IDE integration:** Standalone tool
8. **Mobile access:** Desktop only
9. **Export/sharing:** Internal use only
10. **Advanced analytics:** Basic stats only

---

## 5. Dependencies & Assumptions

### External Dependencies
- **Python:** ≥3.10
- **System:** macOS (initial target; Linux support future)
- **Disk Space:** ~500MB (embeddings + data)
- **RAM:** ≥4GB recommended for clustering
- **Zen Browser:** Installed with accessible profile

### Assumptions
1. User has basic command-line proficiency
2. Browser/shell history available and readable
3. Git repositories use standard .git structure
4. User willing to install ~100MB of dependencies
5. User understands local-first means no cloud backup

---

## 6. Acceptance Criteria (System-Level)

The system is considered functionally complete when:

- [ ] User can run `lk init` and complete setup successfully
- [ ] User can run `lk sync` and ingest data from all 3 sources
- [ ] User can run `lk search "query"` and get relevant results
- [ ] User can run `lk timeline` and see task clusters
- [ ] User can run `lk cluster` and regenerate clusters
- [ ] All P0 and P1 requirements implemented
- [ ] Performance targets met for 90-day history
- [ ] Privacy filters prevent sensitive data storage
- [ ] Documentation covers installation and basic usage
- [ ] Test suite passes with >80% coverage

---

## 7. Future Enhancements (Post-MVP)

Ranked by user value:

1. **Atuin integration** - Better CWD tracking (high value, medium effort)
2. **Multi-browser support** - Chrome, Firefox (medium value, medium effort)
3. **Web UI** - Visual exploration (high value, high effort)
4. **Smart suggestions** - "You might need..." (medium value, high effort)
5. **Export task context** - Share sanitized history (low value, low effort)
6. **IDE history** - VSCode recently opened (medium value, medium effort)
7. **Calendar correlation** - Link meetings to tasks (low value, medium effort)

---

## Appendix A: User Scenarios

### Scenario 1: Finding a Solution
**Context:** Developer fixed a bug last month, can't remember how.

**Flow:**
1. Run: `lk search "redis connection timeout"`
2. Review results showing StackOverflow links, commands tried, final commit
3. Copy working solution from history

**Success:** Found solution in <2 minutes vs 20 minutes of browsing.

---

### Scenario 2: Resuming Work
**Context:** Developer interrupted mid-task, needs context to resume.

**Flow:**
1. Run: `lk timeline --days 7`
2. Identify incomplete cluster: "api-refactor (Nov 12)"
3. Run: `lk timeline --cluster 15 --verbose`
4. Review last commands, docs, commits
5. Resume work with full context

**Success:** Context recovered in <5 minutes vs 30 minutes of reconstruction.

---

### Scenario 3: Retrospective
**Context:** Manager asks "What did you work on last week?"

**Flow:**
1. Run: `lk timeline --days 7`
2. Review cluster list and activity counts
3. Generate summary from cluster labels

**Success:** Quick retrospective in <2 minutes vs incomplete memory.

---

## Appendix B: Test Cases

### TC-1: End-to-End Smoke Test
```bash
# Fresh system
lk init
lk sync --full
lk cluster
lk search "test query"
lk timeline
# All commands succeed, data present
```

### TC-2: Privacy Filter Test
```bash
# Create history with sensitive data
echo ": 1700000000:0;export API_KEY=secret123" >> ~/.zsh_history
lk sync
lk search "API_KEY"
# Result: No sensitive data in results
```

### TC-3: Incremental Sync Test
```bash
lk sync  # Initial sync
# Add new history entries
lk sync  # Incremental
# Result: Only new entries processed
```

### TC-4: Empty Data Test
```bash
# No browser history
lk sync
# Result: Graceful handling, partial success
```

---

## Document Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-11-18 | Initial functional specification | System |
