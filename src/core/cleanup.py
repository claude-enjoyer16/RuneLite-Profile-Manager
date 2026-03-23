"""Cleanup logic for orphaned profile data files."""

import json
from pathlib import Path

from src.utils.paths import PROFILES_JSON


def find_orphaned_files(profiles2_dir: Path) -> list[Path]:
    """Find .properties files in profiles2 with no matching profiles.json entry.

    A .properties file is considered referenced if its name matches
    the pattern name-id.properties for some entry in profiles.json.

    Args:
        profiles2_dir: Path to the profiles2 directory.

    Returns:
        List of paths to orphaned .properties files.
    """
    raw = json.loads(
        (profiles2_dir / PROFILES_JSON).read_text(encoding="utf-8")
    )
    entries = raw["profiles"]

    expected = {
        f"{e['name']}-{e['id']}.properties"
        for e in entries
        if "name" in e and "id" in e
    }

    orphaned = [
        f for f in profiles2_dir.iterdir()
        if f.is_file() and f.suffix == ".properties" and f.name not in expected
    ]

    return sorted(orphaned, key=lambda p: p.name)


def delete_orphaned_files(orphaned: list[Path]) -> None:
    """Delete the given list of orphaned files.

    Args:
        orphaned: List of file paths to delete.
    """
    for f in orphaned:
        f.unlink()
