"""Search page."""

from datetime import datetime, timedelta

import streamlit as st

from linknower.domain import EventType
from linknower.ui.services import ServiceFactory
from linknower.ui.utils import UIState, apply_filters, format_event_card


def render() -> None:
    """Render the search page."""
    st.markdown("## 🔍 Semantic Search")
    st.write("Search your activities by meaning, not just keywords")

    # Initialize services
    config = UIState.get_config()
    if UIState.get_services() is None:
        factory = ServiceFactory(config)
        UIState.set_services(factory.get_services())

    services = UIState.get_services()

    # Search input
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Search query",
            placeholder="e.g., python authentication tutorial",
            label_visibility="collapsed",
        )

    with col2:
        limit = st.number_input("Results", min_value=5, max_value=100, value=10, step=5)

    # Filters
    with st.expander("🔧 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            event_type = st.selectbox(
                "Event Type",
                ["All", "Browser", "Command", "Commit"],
            )

        with col2:
            date_filter = st.selectbox(
                "Date Range",
                ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
            )

        with col3:
            if date_filter == "Custom":
                date_range = st.date_input(
                    "Select dates",
                    value=(datetime.now() - timedelta(days=7), datetime.now()),
                )

    # Search button
    if st.button("🔍 Search", type="primary") or query:
        if not query:
            st.warning("⚠️ Please enter a search query")
            return

        with st.spinner("Searching..."):
            try:
                # Determine event type filter
                et = None
                if event_type != "All":
                    et = EventType(event_type.lower())

                # Perform search
                results = services["search"].search(query, limit=limit, event_type=et)

                if not results:
                    st.info("🔍 No results found")
                    return

                # Apply additional filters
                events = [event for event, score in results]
                scores = {event.id: score for event, score in results}

                # Date filter
                if date_filter != "All Time" and date_filter != "Custom":
                    days_map = {
                        "Last 7 Days": 7,
                        "Last 30 Days": 30,
                        "Last 90 Days": 90,
                    }
                    days = days_map[date_filter]
                    start = datetime.now() - timedelta(days=days)
                    events = [e for e in events if e.timestamp >= start]
                elif date_filter == "Custom" and date_range:
                    start = datetime.combine(date_range[0], datetime.min.time())
                    end = datetime.combine(date_range[1], datetime.max.time())
                    events = [e for e in events if start <= e.timestamp <= end]

                # Display results
                st.markdown(f"### Found {len(events)} results")

                # Results view mode
                view_mode = st.radio(
                    "View as:",
                    ["Cards", "Table"],
                    horizontal=True,
                    label_visibility="collapsed",
                )

                if view_mode == "Cards":
                    # Card view
                    for event in events:
                        score = scores[event.id]
                        with st.container():
                            col1, col2 = st.columns([5, 1])

                            with col1:
                                st.markdown(format_event_card(event))

                            with col2:
                                st.metric("Score", f"{score:.3f}")

                            st.markdown("---")

                else:
                    # Table view
                    import pandas as pd

                    data = []
                    for event in events:
                        score = scores[event.id]
                        data.append(
                            {
                                "Type": event.type.value,
                                "Time": event.timestamp.strftime("%Y-%m-%d %H:%M"),
                                "Content": (
                                    event.content[:80] + "..."
                                    if len(event.content) > 80
                                    else event.content
                                ),
                                "Score": f"{score:.3f}",
                                "CWD": event.cwd[:30] + "..." if event.cwd else "",
                            }
                        )

                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                st.exception(e)

    # Example queries
    with st.expander("💡 Example Queries"):
        st.markdown("""
        Try these example searches:
        
        - `python authentication tutorial`
        - `docker compose setup`
        - `git rebase commands`
        - `react state management`
        - `database migration`
        - `API error handling`
        """)

        if st.button("Try: python authentication"):
            st.rerun()
