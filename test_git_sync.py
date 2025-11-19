#!/usr/bin/env python3
"""Test git sync functionality."""

from pathlib import Path
from linknower.data.parsers import GitParser

repo_path = Path("/Users/harikishore/sources/shastra")

print(f"Testing GitParser on: {repo_path}")
print(f"Repo exists: {repo_path.exists()}")
print(f".git exists: {(repo_path / '.git').exists()}")

if repo_path.exists():
    try:
        parser = GitParser(repo_path)
        events = list(parser.parse())
        print(f"\nFound {len(events)} commits:")
        for i, event in enumerate(events[:5]):  # Show first 5
            print(f"\n{i+1}. {event.timestamp}")
            print(f"   Content: {event.content[:100]}...")
            print(f"   SHA: {event.metadata.get('sha', 'N/A')[:8]}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
