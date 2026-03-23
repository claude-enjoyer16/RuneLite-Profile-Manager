"""Path resolution and validation for RuneLite profiles2 directory."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"id": int, "name": str}

PROFILES_JSON = "profiles.json"


def get_default_profiles2_dir() -> Path | None:
    """Resolve the default profiles2 directory.

    Returns the path if it exists and contains profiles.json, otherwise None.
    """
    profiles2 = Path.home() / ".runelite" / "profiles2"
    if profiles2.is_dir() and (profiles2 / "profiles.json").is_file():
        return profiles2
    return None


def validate_runelite_folder(folder: Path) -> Path:
    """Validate a .runelite folder and return the profiles2 path.

    Args:
        folder: Path to the .runelite directory.

    Returns:
        Path to the profiles2 subdirectory.

    Raises:
        ValueError: If the folder structure or profiles.json is invalid.
    """
    profiles2 = folder / "profiles2"

    if not profiles2.is_dir():
        raise ValueError(f"profiles2 directory not found in {folder}")

    profiles_json = profiles2 / "profiles.json"
    if not profiles_json.is_file():
        raise ValueError(f"profiles.json not found in {profiles2}")

    try:
        data = json.loads(profiles_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"profiles.json is not valid JSON: {e}") from e

    if not isinstance(data, dict) or "profiles" not in data:
        raise ValueError(
            "profiles.json must be a JSON object with a 'profiles' key"
        )

    if not isinstance(data["profiles"], list):
        raise ValueError("profiles.json 'profiles' must be an array")

    return profiles2


def load_profiles_json(profiles2_dir: Path) -> list[dict]:
    """Read and validate profiles.json, returning the list of profile entries.

    Entries missing required fields are skipped with a warning.

    Args:
        profiles2_dir: Path to the profiles2 directory.

    Returns:
        List of valid profile dictionaries.

    Raises:
        ValueError: If profiles.json is missing or malformed.
        OSError: If the file cannot be read.
    """
    profiles_json = profiles2_dir / "profiles.json"

    try:
        raw = json.loads(profiles_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"profiles.json is not valid JSON: {e}") from e

    if not isinstance(raw, dict) or "profiles" not in raw:
        raise ValueError(
            "profiles.json must be a JSON object with a 'profiles' key"
        )

    data = raw["profiles"]
    if not isinstance(data, list):
        raise ValueError("profiles.json 'profiles' must be an array")

    valid_profiles = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            logger.warning("profiles.json entry %d is not a dict, skipping", i)
            continue

        missing = [
            field for field, typ in REQUIRED_FIELDS.items()
            if field not in entry or not isinstance(entry[field], typ)
        ]
        if missing:
            logger.warning(
                "profiles.json entry %d missing or invalid fields %s, skipping",
                i, missing,
            )
            continue

        valid_profiles.append(entry)

    return valid_profiles


def save_profiles_json(profiles2_dir: Path, all_entries: list[dict]) -> None:
    """Write the full profiles list back to profiles.json atomically.

    Args:
        profiles2_dir: Path to the profiles2 directory.
        all_entries: The complete list of profile dicts (including $rsprofile).
    """
    profiles_json = profiles2_dir / PROFILES_JSON
    data = {"profiles": all_entries}
    content = json.dumps(data, indent=2)

    profiles_json.write_text(content, encoding="utf-8")
