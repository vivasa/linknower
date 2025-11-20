"""Data parsers for extracting workflow events from various sources."""

import re
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Iterator

from git import Repo

from linknower.domain import Event, EventType


class EventParser(ABC):
    """Base class for event parsers."""

    @abstractmethod
    def parse(self) -> Iterator[Event]:
        """Parse and yield events."""
        pass


class ZenBrowserParser(EventParser):
    """Parser for Zen Browser (Firefox-based) history."""

    def __init__(self, profile_path: Path):
        """Initialize parser with browser profile path."""
        self.profile_path = profile_path
        self.db_path = profile_path / "places.sqlite"

        if not self.db_path.exists():
            raise FileNotFoundError(f"Browser database not found: {self.db_path}")

    def parse(self) -> Iterator[Event]:
        """Parse browsing history from SQLite database."""
        import shutil
        import tempfile

        # Always copy the database to avoid locking issues with active browser
        # Browser databases are frequently locked, so copying is safer
        temp_db_file = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
        temp_db_file.close()

        try:
            shutil.copy2(self.db_path, temp_db_file.name)
        except Exception as e:
            # Clean up and re-raise
            try:
                Path(temp_db_file.name).unlink()
            except Exception:
                pass
            raise Exception(f"Failed to copy browser database: {e}")

        db_to_use = Path(temp_db_file.name)

        # Connect to the temp database copy
        conn = sqlite3.connect(f"file:{db_to_use}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.cursor()
            # Query moz_places and moz_historyvisits tables
            query = """
                SELECT
                    p.url,
                    p.title,
                    h.visit_date,
                    h.visit_type
                FROM moz_places p
                INNER JOIN moz_historyvisits h ON h.place_id = p.id
                WHERE h.visit_date IS NOT NULL
                ORDER BY h.visit_date
            """

            for row in cursor.execute(query):
                # Firefox stores timestamps as microseconds since epoch
                timestamp = datetime.fromtimestamp(row["visit_date"] / 1_000_000)
                url = row["url"]
                title = row["title"] or url

                # Create content combining title and URL
                content = f"{title} - {url}" if title != url else url

                yield Event(
                    type=EventType.BROWSER,
                    timestamp=timestamp,
                    content=content,
                    metadata={
                        "url": url,
                        "title": title,
                        "visit_type": str(row["visit_type"]),
                    },
                )
        finally:
            conn.close()
            # Clean up temp file
            try:
                Path(temp_db_file.name).unlink()
            except Exception:
                pass


class ZshHistoryParser(EventParser):
    """Parser for zsh shell history."""

    # Extended timestamp format: : <timestamp>:<duration>;<command>
    EXTENDED_PATTERN = re.compile(r"^: (\d+):\d+;(.+)$", re.MULTILINE)
    # Simple format: just the command
    SIMPLE_PATTERN = re.compile(r"^([^:].+)$", re.MULTILINE)

    def __init__(self, history_path: Path, cwd_tracker: "CWDTracker | None" = None):
        """Initialize parser with history file path."""
        self.history_path = history_path
        self.cwd_tracker = cwd_tracker

        if not self.history_path.exists():
            raise FileNotFoundError(f"History file not found: {self.history_path}")

    def parse(self) -> Iterator[Event]:
        """Parse command history from zsh history file."""
        with open(self.history_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Try extended format first (with timestamps)
        for match in self.EXTENDED_PATTERN.finditer(content):
            timestamp_str, command = match.groups()
            timestamp = datetime.fromtimestamp(int(timestamp_str))

            # Infer CWD if tracker is available
            cwd = self.cwd_tracker.infer_cwd(command, timestamp) if self.cwd_tracker else None

            yield Event(
                type=EventType.COMMAND,
                timestamp=timestamp,
                content=command.strip(),
                metadata={"shell": "zsh"},
                cwd=cwd,
            )

        # If no extended format matches, fall back to simple format
        # Use current time with sequential offsets
        if not any(self.EXTENDED_PATTERN.finditer(content)):
            base_time = datetime.now()
            for idx, match in enumerate(self.SIMPLE_PATTERN.finditer(content)):
                command = match.group(1).strip()
                if command:
                    # Use sequential timestamps going backwards
                    timestamp = datetime.fromtimestamp(
                        base_time.timestamp() - (len(content) - idx)
                    )

                    cwd = (
                        self.cwd_tracker.infer_cwd(command, timestamp)
                        if self.cwd_tracker
                        else None
                    )

                    yield Event(
                        type=EventType.COMMAND,
                        timestamp=timestamp,
                        content=command,
                        metadata={"shell": "zsh", "inferred_timestamp": "true"},
                        cwd=cwd,
                    )


class GitParser(EventParser):
    """Parser for git commit history."""

    def __init__(self, repo_path: Path):
        """Initialize parser with repository path."""
        self.repo_path = repo_path

        if not (repo_path / ".git").exists():
            raise FileNotFoundError(f"Not a git repository: {repo_path}")

        self.repo = Repo(repo_path)

    def parse(self) -> Iterator[Event]:
        """Parse commit history from git repository."""
        for commit in self.repo.iter_commits():
            # Create content from commit message and stats
            message = commit.message.strip()
            stats = commit.stats.total

            content_parts = [message]
            if stats.get("files"):
                content_parts.append(f"({stats['files']} files changed)")

            content = " ".join(content_parts)

            yield Event(
                type=EventType.COMMIT,
                timestamp=datetime.fromtimestamp(commit.committed_date),
                content=content,
                metadata={
                    "sha": commit.hexsha,
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "files_changed": str(stats.get("files", 0)),
                    "insertions": str(stats.get("insertions", 0)),
                    "deletions": str(stats.get("deletions", 0)),
                },
                cwd=str(self.repo_path),
            )


class CWDTracker:
    """Tracks and infers current working directory from command history."""

    CD_PATTERN = re.compile(r"^cd\s+(.+)$")

    def __init__(self, home_dir: Path):
        """Initialize tracker with user's home directory."""
        self.home_dir = home_dir
        self.cwd_history: list[tuple[datetime, str]] = []

    def infer_cwd(self, command: str, timestamp: datetime) -> str:
        """Infer CWD for a command based on previous cd commands."""
        # Check if this is a cd command
        match = self.CD_PATTERN.match(command.strip())
        if match:
            target = match.group(1).strip().strip("'\"")

            # Expand ~ to home directory
            if target.startswith("~"):
                target = str(self.home_dir / target[2:] if len(target) > 1 else self.home_dir)
            # Handle absolute vs relative paths
            elif not Path(target).is_absolute():
                # Relative to current CWD
                current_cwd = self._get_cwd_at_time(timestamp)
                target = str(Path(current_cwd) / target)

            # Normalize path
            target = str(Path(target).resolve())

            # Record this cd command
            self.cwd_history.append((timestamp, target))
            return target

        # Not a cd command, return the most recent CWD
        return self._get_cwd_at_time(timestamp)

    def _get_cwd_at_time(self, timestamp: datetime) -> str:
        """Get the CWD at a specific time based on history."""
        # Find the most recent cd before this timestamp
        for cmd_time, cwd in reversed(self.cwd_history):
            if cmd_time <= timestamp:
                return cwd

        # Default to home directory
        return str(self.home_dir)
