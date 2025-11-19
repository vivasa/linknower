# Web UI Guide

## Overview

LinkNower's Streamlit-based web interface provides an intuitive, visual way to explore your workflow intelligence. The UI is designed with modularity, maintainability, and user experience in mind.

## Architecture

### Component Structure

```
src/linknower/ui/
├── app.py                 # Main application (home, navigation, layout)
├── services.py            # Service factory (dependency injection)
├── utils.py               # Shared utilities (state, formatting, filters)
└── pages/
    ├── search.py          # Semantic search interface
    ├── timeline.py        # Timeline visualization
    └── clusters.py        # Cluster exploration
```

### Design Principles

1. **Separation of Concerns**: Each page is self-contained
2. **Reusable Components**: Shared utilities in `utils.py`
3. **Service Layer**: All business logic delegated to services
4. **Session State Management**: Centralized via `UIState` class
5. **Factory Pattern**: `ServiceFactory` for dependency injection

## Features

### 🏠 Home Page

**Purpose**: Welcome screen with navigation and quick actions

**Components:**
- Quick stats sidebar
- Feature cards (Search, Timeline, Clusters)
- Sync control panel
- Configuration overview

**Key Functions:**
- One-click data sync
- Real-time statistics
- Navigation to main features

### 🔍 Search Page

**Purpose**: Semantic search with advanced filtering

**Features:**
- **Search Box**: Natural language queries
- **Type Filter**: Browser/Command/Commit
- **Date Filters**: Last 7/30/90 days, custom range
- **View Modes**: Card view (detailed) or Table view (compact)
- **Scoring**: Similarity scores for each result
- **Example Queries**: Quick start templates

**User Flow:**
1. Enter query (e.g., "python authentication")
2. Apply filters (optional)
3. View results in preferred format
4. Click events for full details

**Technical Details:**
- Uses `SearchService` for semantic search
- Applies filters client-side for responsiveness
- Displays similarity scores (0-1 range)
- Supports pagination for large result sets

### 📅 Timeline Page

**Purpose**: Chronological activity browser with visualizations

**Features:**
- **Date Range Selector**: 7/30 days, custom, specific date
- **Event Type Filter**: Multi-select (browser, command, commit)
- **Directory Filter**: Filter by CWD
- **Visualizations**:
  - Timeline scatter plot (events over time)
  - Hourly activity bar chart
- **Pagination**: 20 events per page

**Visualizations:**
1. **Timeline View**: Plotly scatter plot showing events chronologically
2. **Hourly Activity**: Bar chart showing activity distribution by hour
3. **Event List**: Detailed card view with pagination

**User Flow:**
1. Select date range
2. Apply filters
3. Choose visualization mode
4. Browse paginated results

**Technical Details:**
- Uses `TimelineService` for data retrieval
- Plotly for interactive charts
- Pandas for data manipulation
- Client-side filtering for performance

### 🧩 Clusters Page

**Purpose**: Discover and explore activity patterns

**Features:**
- **Cluster Generation**: One-click UMAP + HDBSCAN clustering
- **Overview Visualization**: Bar chart of cluster sizes
- **Sorting**: By event count, date (recent/oldest)
- **Cluster Details**: Expandable cards with:
  - Event count
  - Time range
  - Duration
  - Representative events
- **Parameter Display**: Shows ML configuration

**User Flow:**
1. Click "Run Clustering" (if needed)
2. View cluster statistics
3. Explore visualization
4. Expand clusters for details
5. Read representative events

**Technical Details:**
- Uses `ClusterService` for generation
- Shows clustering parameters (min_cluster_size, weights)
- Representative events from cluster metadata
- Noise events tracked separately

## State Management

### Session State

Managed via `UIState` class in `utils.py`:

```python
class UIState:
    @staticmethod
    def init_session_state() -> None
        """Initialize all session variables"""
    
    @staticmethod
    def get_config() -> Config
        """Get application config"""
    
    @staticmethod
    def set_services(services: dict) -> None
        """Cache services for reuse"""
```

**Stored State:**
- `config`: Application configuration
- `services`: Service instances (lazy-loaded)
- `last_sync`: Last sync timestamp

**Benefits:**
- Avoids re-initialization on every interaction
- Preserves state across page changes
- Reduces loading times

## Service Factory

The `ServiceFactory` implements dependency injection:

```python
class ServiceFactory:
    def __init__(self, config: Config)
    def get_services() -> dict
    def refresh_services() -> None
```

**Responsibilities:**
- Initialize repositories (SQLite, ChromaDB)
- Create ML components (embedding, clustering)
- Wire up application services
- Provide refresh mechanism

**Benefits:**
- Single source of truth for service creation
- Testable (can inject mock services)
- Loosely coupled components
- Easy to extend

## Utility Functions

### Formatting

- `event_to_dict()`: Convert Event to dict for DataFrames
- `events_to_dataframe()`: Batch conversion to pandas
- `format_event_card()`: Markdown card with emoji icons
- `get_event_type_color()`: Consistent color scheme

### Filtering

- `apply_filters()`: Unified filtering logic
  - Type filter (browser/command/commit)
  - Date range filter
  - CWD filter

### Messaging

- `show_error()`: Consistent error styling
- `show_success()`: Success messages
- `show_info()`: Informational messages
- `show_warning()`: Warning messages

## Styling

### Custom CSS

Applied in `app.py`:

```css
.main-header: Large, bold title
.subtitle: Descriptive subheading
.metric-card: Highlighted metric boxes
```

### Color Scheme

- **Browser**: Blue (#3b82f6)
- **Command**: Green (#10b981)
- **Commit**: Amber (#f59e0b)
- **Neutral**: Gray (#6b7280)

### Layout

- **Wide Layout**: Maximizes screen real estate
- **Expandable Sidebar**: Persistent controls
- **Column-based**: Responsive grid layout
- **Tabs**: Organized feature separation

## Performance Optimizations

1. **Lazy Loading**: Services initialized on first use
2. **Session Caching**: Services reused across page changes
3. **Client-side Filtering**: Reduces backend calls
4. **Pagination**: Limits rendered events
5. **Batch Operations**: DataFrames for bulk processing

## Error Handling

All pages implement try-except blocks:

```python
try:
    # Operation
    results = service.operation()
    st.success("Success!")
except Exception as e:
    st.error(f"Failed: {str(e)}")
    st.exception(e)  # Show traceback in debug
```

**User Experience:**
- Friendly error messages
- Detailed exceptions in expandable sections
- Graceful degradation (no crashes)

## Extensibility

### Adding a New Page

1. Create `src/linknower/ui/pages/new_feature.py`:
```python
def render() -> None:
    """Render the new feature page."""
    st.markdown("## New Feature")
    # Implementation
```

2. Add tab in `app.py`:
```python
with tab_new:
    from linknower.ui.pages import new_feature
    new_feature.render()
```

3. Update navigation in home page

### Adding a New Service

1. Implement service in `linknower/services/`
2. Add to `ServiceFactory._initialize_services()`
3. Use in pages via `UIState.get_services()`

### Custom Visualizations

Use Plotly for interactive charts:

```python
import plotly.express as px

fig = px.scatter(df, x="time", y="type")
st.plotly_chart(fig, use_container_width=True)
```

## Running the UI

### Development

```bash
# With hot-reload
streamlit run src/linknower/ui/app.py

# Specify port
streamlit run src/linknower/ui/app.py --server.port 8502
```

### Production

```bash
# Convenience script
./launch_ui.sh

# Or with optimizations
streamlit run src/linknower/ui/app.py \
    --server.headless true \
    --server.enableCORS false
```

### Configuration

Create `.streamlit/config.toml`:

```toml
[server]
port = 8501
enableCORS = false
headless = true

[theme]
primaryColor = "#3b82f6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8f9fa"
textColor = "#262730"
font = "sans serif"
```

## Keyboard Shortcuts

Streamlit provides built-in shortcuts:

- `R`: Rerun app
- `C`: Clear cache
- `⌘/Ctrl + K`: Command palette
- `⌘/Ctrl + Enter`: Submit form

## Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -ti:8501

# Kill process
kill -9 $(lsof -ti:8501)
```

### Import Errors

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

### Slow Performance

1. Reduce data volume (sync less frequently)
2. Increase pagination size
3. Use table view instead of card view
4. Clear Streamlit cache (press 'C')

## Best Practices

### Code Organization

✅ **Do:**
- Keep pages focused on single feature
- Extract reusable logic to utils
- Use services for business logic
- Implement error boundaries

❌ **Don't:**
- Mix business logic in UI code
- Duplicate filtering logic
- Store sensitive data in session state
- Ignore exceptions

### User Experience

✅ **Do:**
- Show loading spinners for long operations
- Provide clear error messages
- Use consistent styling
- Add helpful tooltips

❌ **Don't:**
- Block UI during operations
- Show raw stack traces to users
- Use technical jargon
- Hide important controls

### Performance

✅ **Do:**
- Cache expensive operations
- Use pagination for large datasets
- Filter client-side when possible
- Lazy-load services

❌ **Don't:**
- Load all data at once
- Re-create services on every interaction
- Perform heavy computation in render loop
- Ignore memory usage

## Future Enhancements

Potential additions:

1. **Export Features**: Download search results as CSV
2. **Event Editing**: Tag, annotate, or delete events
3. **Custom Dashboards**: User-configurable layouts
4. **Activity Heatmaps**: Calendar view of activity
5. **Graph View**: Network visualization of related events
6. **Saved Searches**: Bookmark frequent queries
7. **Themes**: Light/dark mode toggle
8. **Keyboard Navigation**: Power user shortcuts

---

**The UI follows clean architecture principles with clear separation between presentation, application logic, and data access. Every component is designed for maintainability and extensibility.**
