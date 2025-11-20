"""Configuration management for LinkNower."""

import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LINKNOWER_",
        env_file=".env",
        case_sensitive=False,
    )

    # Data paths
    data_dir: Path = Field(default=Path.home() / ".linknower")
    zen_profile_path: str = Field(
        default="~/Library/Application Support/Zen/Profiles/*default*"
    )
    zsh_history_path: str = Field(default="~/.zsh_history")
    git_repos: list[str] = Field(default_factory=list)

    # Database paths
    raw_db_path: Optional[Path] = None
    cluster_db_path: Optional[Path] = None
    chroma_db_path: Optional[Path] = None

    # ML settings
    embedding_model: str = "all-MiniLM-L6-v2"
    min_cluster_size: int = 5
    time_weight: float = 0.3
    semantic_weight: float = 0.5
    context_weight: float = 0.2

    # Privacy settings
    privacy_patterns: list[str] = Field(
        default_factory=lambda: [
            r"password\s*=\s*['\"]?[\w]+['\"]?",
            r"api[_-]?key\s*=\s*['\"]?[\w]+['\"]?",
            r"token\s*=\s*['\"]?[\w]+['\"]?",
            r"secret\s*=\s*['\"]?[\w]+['\"]?",
            r"aws[_-]?access[_-]?key",
            r"private[_-]?key",
        ]
    )

    def __init__(self, **data):
        """Initialize config and set up derived paths."""
        super().__init__(**data)

        # Set up derived paths
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.raw_db_path is None:
            self.raw_db_path = self.data_dir / "raw.db"

        if self.cluster_db_path is None:
            self.cluster_db_path = self.data_dir / "clusters.db"

        if self.chroma_db_path is None:
            self.chroma_db_path = self.data_dir / "chroma"

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        data = {
            "zen_profile_path": self.zen_profile_path,
            "zsh_history_path": self.zsh_history_path,
            "git_repos": self.git_repos,
            "embedding_model": self.embedding_model,
            "min_cluster_size": self.min_cluster_size,
            "time_weight": self.time_weight,
            "semantic_weight": self.semantic_weight,
            "context_weight": self.context_weight,
            "privacy_patterns": self.privacy_patterns,
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def add_git_repo(self, repo_path: str) -> None:
        """Add a git repository to monitor."""
        if repo_path not in self.git_repos:
            self.git_repos.append(repo_path)

    def get_config_path(self) -> Path:
        """Get the default config file path."""
        return self.data_dir / "config.yaml"


class PrivacyFilter:
    """Filters sensitive information from events."""

    def __init__(self, patterns: list[str]):
        """Initialize with regex patterns for sensitive data."""
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    def is_allowed(self, content: str) -> bool:
        """Check if content is allowed (doesn't contain sensitive data)."""
        for pattern in self.patterns:
            if pattern.search(content):
                return False
        return True

    def redact(self, content: str, replacement: str = "[REDACTED]") -> str:
        """Redact sensitive information from content."""
        result = content
        for pattern in self.patterns:
            result = pattern.sub(replacement, result)
        return result
