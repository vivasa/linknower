"""Main Streamlit application."""

import streamlit as st

from linknower.ui.services import ServiceFactory
from linknower.ui.utils import UIState

# Page configuration
st.set_page_config(
    page_title="LinkNower",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
UIState.init_session_state()

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown('<div class="main-header">🔍 LinkNower</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Local-first Personal Workflow Intelligence</div>',
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")

    # Configuration status
    config = UIState.get_config()
    config_path = config.get_config_path()

    if config_path.exists():
        st.success("✅ Configuration loaded")
    else:
        st.warning("⚠️ Configuration not found")
        if st.button("Initialize Config"):
            config.to_file(config_path)
            st.rerun()

    st.markdown("---")

    # Data sync
    st.markdown("### 🔄 Data Sync")

    if st.button("🔄 Sync Now", type="primary"):
        with st.spinner("Syncing data..."):
            try:
                # Initialize services if needed
                if UIState.get_services() is None:
                    factory = ServiceFactory(config)
                    UIState.set_services(factory.get_services())

                services = UIState.get_services()
                stats = services["sync"].sync_all(full=False)

                st.success("✅ Sync completed!")
                st.write(f"Browser: {stats['browser']}")
                st.write(f"Commands: {stats['command']}")
                st.write(f"Commits: {stats['commit']}")

            except Exception as e:
                st.error(f"❌ Sync failed: {str(e)}")

    st.markdown("---")

    # Quick stats
    st.markdown("### 📊 Quick Stats")

    try:
        if UIState.get_services() is None:
            factory = ServiceFactory(config)
            UIState.set_services(factory.get_services())

        services = UIState.get_services()
        stats = services["stats"].get_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Events", f"{stats['total_events']:,}")
        with col2:
            st.metric("Clusters", f"{stats['total_clusters']:,}")

        st.metric("Browser Events", f"{stats['browser_events']:,}")
        st.metric("Command Events", f"{stats['command_events']:,}")
        st.metric("Commit Events", f"{stats['commit_events']:,}")

    except Exception as e:
        st.info("Run a sync to see stats")

    st.markdown("---")

    # Configuration
    st.markdown("### ⚙️ Settings")

    if st.button("📝 Edit Config"):
        st.info(f"Config file: `{config_path}`")

    if st.button("🔧 View Paths"):
        st.code(f"""
Data Directory: {config.data_dir}
Browser Profile: {config.zen_profile_path}
Zsh History: {config.zsh_history_path}
Git Repos: {len(config.git_repos)}
        """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "🔍 Search", "📅 Timeline", "🧩 Clusters"])

with tab1:
    st.markdown("## Welcome to LinkNower")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔍 Semantic Search")
        st.write("Find activities by meaning, not just keywords")
        if st.button("Go to Search →", key="nav_search"):
            st.info("Navigate to Search tab above")

    with col2:
        st.markdown("### 📅 Timeline View")
        st.write("Browse your activities chronologically")
        if st.button("Go to Timeline →", key="nav_timeline"):
            st.info("Navigate to Timeline tab above")

    with col3:
        st.markdown("### 🧩 Clusters")
        st.write("Discover patterns in your workflow")
        if st.button("Go to Clusters →", key="nav_clusters"):
            st.info("Navigate to Clusters tab above")

    st.markdown("---")

    st.markdown("## 🚀 Quick Start")

    with st.expander("📖 How to use LinkNower"):
        st.markdown("""
        1. **Sync Your Data**: Click "Sync Now" in the sidebar to index your activities
        2. **Search**: Use semantic search to find what you're looking for
        3. **Explore Timeline**: Browse your activities by date
        4. **Discover Clusters**: See patterns in your workflow

        ### Privacy & Security
        - ✅ All data stays local on your machine
        - ✅ No cloud sync, no tracking
        - ✅ Sensitive data automatically filtered
        """)

    with st.expander("⚙️ Configuration"):
        st.markdown(f"""
        **Configuration File**: `{config_path}`

        **Data Sources**:
        - Zen Browser: `{config.zen_profile_path}`
        - Zsh History: `{config.zsh_history_path}`
        - Git Repositories: {len(config.git_repos)} configured

        **ML Settings**:
        - Embedding Model: {config.embedding_model}
        - Min Cluster Size: {config.min_cluster_size}
        """)

with tab2:
    from linknower.ui.pages import search

    search.render()

with tab3:
    from linknower.ui.pages import timeline

    timeline.render()

with tab4:
    from linknower.ui.pages import clusters

    clusters.render()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    LinkNower v0.2.0 | Local-first Workflow Intelligence | 
    <a href='https://github.com/linknower/linknower'>GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
