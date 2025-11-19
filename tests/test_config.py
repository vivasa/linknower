"""Tests for configuration."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from linknower.utils import Config, PrivacyFilter


def test_config_defaults():
    """Test default configuration values."""
    config = Config()

    assert config.data_dir == Path.home() / ".linknower"
    assert config.embedding_model == "all-MiniLM-L6-v2"
    assert config.min_cluster_size == 5
    assert config.time_weight == 0.3
    assert config.semantic_weight == 0.5
    assert config.context_weight == 0.2


def test_config_file_operations():
    """Test saving and loading configuration."""
    with TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        # Create and save config
        config = Config(
            data_dir=Path(tmpdir),
            min_cluster_size=10,
        )
        config.to_file(config_path)

        # Load config
        loaded_config = Config.from_file(config_path)

        assert loaded_config.min_cluster_size == 10
        assert loaded_config.embedding_model == "all-MiniLM-L6-v2"


def test_privacy_filter():
    """Test privacy filtering."""
    patterns = [
        r"password\s*=\s*['\"]?[\w]+['\"]?",
        r"api[_-]?key\s*=\s*['\"]?[\w]+['\"]?",
    ]

    filter = PrivacyFilter(patterns)

    # Should block
    assert not filter.is_allowed("export password=secret123")
    assert not filter.is_allowed("API_KEY=abc123")

    # Should allow
    assert filter.is_allowed("git commit -m 'fix bug'")
    assert filter.is_allowed("https://example.com")


def test_privacy_filter_redaction():
    """Test privacy filter redaction."""
    patterns = [r"password\s*=\s*['\"]?[\w]+['\"]?"]
    filter = PrivacyFilter(patterns)

    content = "export password=secret123 and some other text"
    redacted = filter.redact(content)

    assert "secret123" not in redacted
    assert "[REDACTED]" in redacted
    assert "some other text" in redacted
