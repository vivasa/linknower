#!/usr/bin/env python3
"""Test browser profile glob pattern fix."""

import glob
from pathlib import Path

# Test the pattern expansion
zen_profile_path = "~/Library/Application Support/Zen/Profiles/*"

# Expand user home directory first
profile_pattern = str(Path(zen_profile_path).expanduser())
print(f"Profile pattern: {profile_pattern}")

# Use glob to resolve wildcard patterns
matching_profiles = glob.glob(profile_pattern)
print(f"\nMatching profiles found: {len(matching_profiles)}")

for i, profile in enumerate(matching_profiles, 1):
    profile_path = Path(profile)
    db_path = profile_path / "places.sqlite"
    print(f"\n{i}. {profile_path.name}")
    print(f"   Path: {profile_path}")
    print(f"   Database exists: {db_path.exists()}")

if matching_profiles:
    print(f"\n✓ Would use: {matching_profiles[0]}")
else:
    print(f"\n✗ No profiles found matching: {profile_pattern}")
