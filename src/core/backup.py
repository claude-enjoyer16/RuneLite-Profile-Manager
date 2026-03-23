"""Backup logic for the profiles2 directory."""

import shutil
from datetime import datetime
from pathlib import Path


def create_backup(profiles2_dir: Path) -> Path:
    """Create a timestamped folder backup of profiles2 inside .runelite.

    Copies the entire profiles2 directory to a sibling folder named
    profiles2-backupYYYYMMDDHHMMSS.

    Args:
        profiles2_dir: Path to the profiles2 directory.

    Returns:
        Path to the created backup folder.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_name = f"profiles2-backup{timestamp}"
    backup_dir = profiles2_dir.parent / backup_name

    shutil.copytree(profiles2_dir, backup_dir)

    return backup_dir
