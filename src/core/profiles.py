"""Profile management: loading, duplicating, and deleting profiles."""

import json
import logging
import re
import shutil
import time
from pathlib import Path

from src.utils.paths import (
    load_profiles_json,
    save_profiles_json,
    PROFILES_JSON,
)

logger = logging.getLogger(__name__)


def load_profiles(profiles2_dir: Path) -> list[dict]:
    """Load and return all user profiles from profiles.json.

    Filters out the system $rsprofile entry (id == -1).
    """
    all_profiles = load_profiles_json(profiles2_dir)
    return [p for p in all_profiles if p.get("id") != -1]


def _next_copy_name(base_name: str, existing_names: set[str]) -> str:
    """Generate the next available copy name.

    wheel -> wheel (1) -> wheel (2), etc.
    If the base already ends with ' (N)', strip it first so we don't get
    'wheel (1) (1)'.
    """
    # Strip existing (N) suffix to get the true base.
    match = re.match(r"^(.*?)\s*\(\d+\)$", base_name)
    root = match.group(1) if match else base_name

    n = 1
    while True:
        candidate = f"{root} ({n})"
        if candidate not in existing_names:
            return candidate
        n += 1


def duplicate_profile(profiles2_dir: Path, profile: dict) -> dict:
    """Duplicate a profile, creating a new .properties file and JSON entry.

    ID is generated via time.monotonic_ns() to match RuneLite's
    System.nanoTime() approach. The .properties file is copied as
    name-id.properties.

    Args:
        profiles2_dir: Path to the profiles2 directory.
        profile: The profile dict to duplicate.

    Returns:
        The new profile dict that was created.
    """
    profiles_json = profiles2_dir / PROFILES_JSON
    raw = json.loads(profiles_json.read_text(encoding="utf-8"))
    all_entries = raw["profiles"]

    existing_names = {e["name"] for e in all_entries}
    new_name = _next_copy_name(profile["name"], existing_names)
    new_id = time.monotonic_ns()

    new_profile = {
        "id": new_id,
        "name": new_name,
        "sync": False,
        "active": False,
        "rev": -1,
        "defaultForRsProfiles": [],
    }

    # Copy the .properties file if it exists.
    src_props = profiles2_dir / f"{profile['name']}-{profile['id']}.properties"
    dst_props = profiles2_dir / f"{new_name}-{new_id}.properties"
    if src_props.is_file():
        shutil.copy2(src_props, dst_props)

    all_entries.append(new_profile)
    save_profiles_json(profiles2_dir, all_entries)

    return new_profile


def delete_profile(profiles2_dir: Path, profile: dict) -> None:
    """Remove a profile entry from profiles.json.

    Args:
        profiles2_dir: Path to the profiles2 directory.
        profile: The profile dict to delete.

    Raises:
        ValueError: If profiles.json cannot be parsed.
        OSError: If profiles.json cannot be read or written.
    """
    profiles_json = profiles2_dir / PROFILES_JSON
    raw = json.loads(profiles_json.read_text(encoding="utf-8"))
    all_entries = raw["profiles"]

    target_id = profile["id"]
    updated = [e for e in all_entries if e.get("id") != target_id]

    save_profiles_json(profiles2_dir, updated)
