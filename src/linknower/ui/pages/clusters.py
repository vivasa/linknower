"""Clusters page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from linknower.ui.services import ServiceFactory
from linknower.ui.utils import UIState, format_event_card


def render() -> None:
    """Render the clusters page."""
    st.markdown("## 🧩 Activity Clusters")
    st.write("Discover patterns and related activities in your workflow")

    # Initialize services
    config = UIState.get_config()
    if UIState.get_services() is None:
        factory = ServiceFactory(config)
        UIState.set_services(factory.get_services())

    services = UIState.get_services()

    # Clustering control
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Run Clustering")
        st.write("Generate clusters from your activities using UMAP + HDBSCAN")

    with col2:
        if st.button("🧩 Run Clustering", type="primary"):
            with st.spinner("Clustering events... This may take a minute."):
                try:
                    stats = services["cluster"].cluster_events()
                    st.success(f"✅ Found {stats['clusters']} clusters!")
                    st.info(f"ℹ️ {stats['noise']} events marked as noise")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Clustering failed: {str(e)}")

    st.markdown("---")

    # Display clusters
    try:
        clusters = services["cluster"].get_all_clusters()

        if not clusters:
            st.info("🧩 No clusters yet. Run clustering to generate them.")
            return

        # Cluster stats
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Clusters", len(clusters))

        with col2:
            total_events = sum(c.event_count for c in clusters)
            st.metric("Clustered Events", total_events)

        with col3:
            avg_size = total_events / len(clusters) if clusters else 0
            st.metric("Avg Cluster Size", f"{avg_size:.1f}")

        st.markdown("---")

        # Cluster visualization
        st.markdown("### Cluster Overview")

        # Prepare data for visualization
        cluster_data = []
        for cluster in clusters:
            duration = (cluster.end_time - cluster.start_time).total_seconds() / 3600
            cluster_data.append(
                {
                    "ID": cluster.id,
                    "Label": cluster.label,
                    "Events": cluster.event_count,
                    "Duration (hours)": duration,
                    "Start": cluster.start_time,
                }
            )

        df = pd.DataFrame(cluster_data)

        # Bar chart of cluster sizes
        fig = px.bar(
            df,
            x="Label",
            y="Events",
            color="Duration (hours)",
            title="Cluster Sizes",
            hover_data=["ID", "Start"],
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Cluster details
        st.markdown("### Cluster Details")

        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            ["Event Count (High to Low)", "Event Count (Low to High)", "Most Recent", "Oldest"],
        )

        if "High to Low" in sort_by:
            clusters_sorted = sorted(clusters, key=lambda c: c.event_count, reverse=True)
        elif "Low to High" in sort_by:
            clusters_sorted = sorted(clusters, key=lambda c: c.event_count)
        elif "Most Recent" in sort_by:
            clusters_sorted = sorted(clusters, key=lambda c: c.end_time, reverse=True)
        else:
            clusters_sorted = sorted(clusters, key=lambda c: c.start_time)

        # Display each cluster
        for cluster in clusters_sorted:
            with st.expander(
                f"🧩 Cluster {cluster.id}: {cluster.label} ({cluster.event_count} events)"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Start:** {cluster.start_time.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Event Count:** {cluster.event_count}")

                with col2:
                    st.write(f"**End:** {cluster.end_time.strftime('%Y-%m-%d %H:%M')}")
                    duration = cluster.end_time - cluster.start_time
                    hours = duration.total_seconds() / 3600
                    st.write(f"**Duration:** {hours:.1f} hours")

                st.markdown("---")

                # Representative events
                if cluster.representative_events:
                    st.markdown("**Representative Events:**")

                    # Get event details from repository
                    event_repo = services["timeline"].event_repo

                    for event_id in cluster.representative_events[:3]:
                        event = event_repo.get_by_id(event_id)
                        if event:
                            st.markdown(format_event_card(event))
                            st.markdown("")

                # View all events button
                if st.button(f"View All {cluster.event_count} Events", key=f"view_{cluster.id}"):
                    st.info(
                        "Navigate to Timeline and filter by cluster (feature coming soon)"
                    )

    except Exception as e:
        st.error(f"❌ Failed to load clusters: {str(e)}")
        st.exception(e)

    # Clustering info
    with st.expander("ℹ️ About Clustering"):
        st.markdown(f"""
        **How it works:**
        
        LinkNower uses advanced ML to group related activities:
        
        1. **Feature Engineering**: Combines temporal, semantic, and contextual signals
        2. **UMAP**: Reduces high-dimensional embeddings to 5D
        3. **HDBSCAN**: Finds density-based clusters (no need to specify number)
        
        **Parameters:**
        - Min Cluster Size: {config.min_cluster_size}
        - Time Weight: {config.time_weight}
        - Semantic Weight: {config.semantic_weight}
        - Context Weight: {config.context_weight}
        
        **Noise events** are activities that don't fit into any cluster pattern.
        """)
