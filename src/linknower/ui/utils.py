"""UI utilities and shared components."""

from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from linknower.domain import Event, EventType
from linknower.utils import Config


class UIState:
    """Manages UI session state."""

    @staticmethod
    def init_session_state() -> None:
        """Initialize session state variables."""
        if "config" not in st.session_state:
            st.session_state.config = Config()

        if "services" not in st.session_state:
            st.session_state.services = None

        if "last_sync" not in st.session_state:
            st.session_state.last_sync = None

    @staticmethod
    def get_config() -> Config:
        """Get configuration from session state."""
        return st.session_state.config

    @staticmethod
    def set_services(services: dict) -> None:
        """Store services in session state."""
        st.session_state.services = services

    @staticmethod
    def get_services() -> Optional[dict]:
        """Get services from session state."""
        return st.session_state.services


def event_to_dict(event: Event) -> dict:
    """Convert Event to dictionary for DataFrame."""
    return {
        "Type": event.type.value,
        "Time": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "Content": event.content,
        "CWD": event.cwd or "",
        "Cluster": event.cluster_id if event.cluster_id is not None else -1,
        "ID": str(event.id),
    }


def events_to_dataframe(events: list[Event]) -> pd.DataFrame:
    """Convert list of Events to pandas DataFrame."""
    if not events:
        return pd.DataFrame()

    data = [event_to_dict(e) for e in events]
    return pd.DataFrame(data)


def format_event_card(event: Event) -> str:
    """Format event as a card with markdown."""
    type_emoji = {
        EventType.BROWSER: "🌐",
        EventType.COMMAND: "⌨️",
        EventType.COMMIT: "📝",
    }

    emoji = type_emoji.get(event.type, "📄")
    time_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    card = f"""
**{emoji} {event.type.value.title()}** | {time_str}

{event.content}
"""

    if event.cwd:
        card += f"\n📁 `{event.cwd}`"

    if event.cluster_id is not None:
        card += f"\n🧩 Cluster: {event.cluster_id}"

    return card


def apply_filters(
    events: list[Event],
    event_type: Optional[str] = None,
    date_range: Optional[tuple[datetime, datetime]] = None,
    cwd_filter: Optional[str] = None,
) -> list[Event]:
    """Apply filters to events list."""
    filtered = events

    # Type filter
    if event_type and event_type != "All":
        filtered = [e for e in filtered if e.type.value == event_type.lower()]

    # Date range filter
    if date_range:
        start, end = date_range
        filtered = [
            e
            for e in filtered
            if start <= e.timestamp <= end.replace(hour=23, minute=59, second=59)
        ]

    # CWD filter
    if cwd_filter:
        filtered = [e for e in filtered if e.cwd and cwd_filter in e.cwd]

    return filtered


def get_event_type_color(event_type: EventType) -> str:
    """Get color for event type."""
    colors = {
        EventType.BROWSER: "#3b82f6",  # blue
        EventType.COMMAND: "#10b981",  # green
        EventType.COMMIT: "#f59e0b",  # amber
    }
    return colors.get(event_type, "#6b7280")


def show_error(message: str) -> None:
    """Show error message with consistent styling."""
    st.error(f"❌ {message}")


def show_success(message: str) -> None:
    """Show success message with consistent styling."""
    st.success(f"✅ {message}")


def show_info(message: str) -> None:
    """Show info message with consistent styling."""
    st.info(f"ℹ️ {message}")


def show_warning(message: str) -> None:
    """Show warning message with consistent styling."""
    st.warning(f"⚠️ {message}")
