"""Timeline page."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from linknower.ui.services import ServiceFactory
from linknower.ui.utils import UIState, apply_filters, format_event_card, get_event_type_color


def render() -> None:
    """Render the timeline page."""
    st.markdown("## 📅 Contextual Timeline")
    st.write("Browse your activities chronologically")

    # Initialize services
    config = UIState.get_config()
    if UIState.get_services() is None:
        factory = ServiceFactory(config)
        UIState.set_services(factory.get_services())

    services = UIState.get_services()

    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        date_option = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 30 Days", "Custom Date", "Specific Date"],
        )

    with col2:
        if date_option == "Custom Date":
            date_range = st.date_input(
                "Select range",
                value=(datetime.now() - timedelta(days=7), datetime.now()),
            )
        elif date_option == "Specific Date":
            specific_date = st.date_input("Select date", value=datetime.now())

    with col3:
        st.write("")  # Spacing

    # Filters
    with st.expander("🔧 Filters", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            event_types = st.multiselect(
                "Event Types",
                ["browser", "command", "commit"],
                default=["browser", "command", "commit"],
            )

        with col2:
            cwd_filter = st.text_input("Filter by directory", placeholder="e.g., /projects/myapp")

    # Load timeline
    with st.spinner("Loading timeline..."):
        try:
            # Determine date range
            if date_option == "Last 7 Days":
                start = None
                end = None
                days = 7
            elif date_option == "Last 30 Days":
                start = None
                end = None
                days = 30
            elif date_option == "Custom Date":
                start = datetime.combine(date_range[0], datetime.min.time())
                end = datetime.combine(date_range[1], datetime.max.time())
                days = None
            else:  # Specific Date
                start = datetime.combine(specific_date, datetime.min.time())
                end = datetime.combine(specific_date, datetime.max.time())
                days = None

            # Get timeline
            events = services["timeline"].get_timeline(start=start, end=end, days=days)

            # Apply filters
            if event_types:
                events = [e for e in events if e.type.value in event_types]

            if cwd_filter:
                events = [e for e in events if e.cwd and cwd_filter in e.cwd]

            if not events:
                st.info("📅 No events found in this time range")
                return

            # Display stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Events", len(events))

            with col2:
                unique_days = len(set(e.timestamp.date() for e in events))
                st.metric("Days with Activity", unique_days)

            with col3:
                if events:
                    duration = events[-1].timestamp - events[0].timestamp
                    hours = duration.total_seconds() / 3600
                    st.metric("Time Span", f"{hours:.1f}h")

            st.markdown("---")

            # Visualization
            view_mode = st.radio(
                "View Mode",
                ["Timeline", "Hourly Activity", "Event List"],
                horizontal=True,
            )

            if view_mode == "Timeline":
                # Create timeline visualization
                df_data = []
                for event in events:
                    df_data.append(
                        {
                            "Time": event.timestamp,
                            "Type": event.type.value.title(),
                            "Content": (
                                event.content[:50] + "..."
                                if len(event.content) > 50
                                else event.content
                            ),
                            "Hour": event.timestamp.hour,
                        }
                    )

                df = pd.DataFrame(df_data)

                fig = px.scatter(
                    df,
                    x="Time",
                    y="Type",
                    color="Type",
                    hover_data=["Content"],
                    title="Activity Timeline",
                    height=400,
                )

                fig.update_traces(marker=dict(size=10))
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Event Type",
                    showlegend=True,
                )

                st.plotly_chart(fig, use_container_width=True)

            elif view_mode == "Hourly Activity":
                # Hourly distribution
                hours = [e.timestamp.hour for e in events]
                df_hours = pd.DataFrame({"Hour": hours})
                hourly_counts = df_hours["Hour"].value_counts().sort_index()

                fig = px.bar(
                    x=hourly_counts.index,
                    y=hourly_counts.values,
                    labels={"x": "Hour of Day", "y": "Event Count"},
                    title="Activity by Hour",
                    height=400,
                )

                st.plotly_chart(fig, use_container_width=True)

            # Event list
            st.markdown("### Event List")

            # Pagination
            events_per_page = 20
            total_pages = (len(events) + events_per_page - 1) // events_per_page

            page = st.number_input(
                f"Page (1-{total_pages})", min_value=1, max_value=total_pages, value=1
            )

            start_idx = (page - 1) * events_per_page
            end_idx = min(start_idx + events_per_page, len(events))

            page_events = events[start_idx:end_idx]

            for event in page_events:
                with st.container():
                    st.markdown(format_event_card(event))
                    st.markdown("---")

            # Navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if page > 1:
                    if st.button("← Previous"):
                        st.rerun()

            with col3:
                if page < total_pages:
                    if st.button("Next →"):
                        st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to load timeline: {str(e)}")
            st.exception(e)
