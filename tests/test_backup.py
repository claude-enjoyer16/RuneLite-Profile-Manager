"""Tests for src.core.backup."""

import json
from unittest.mock import patch
from datetime import datetime

from src.core.backup import create_backup


def _make_profiles2(tmp_path):
    profiles2 = tmp_path / ".runelite" / "profiles2"
    profiles2.mkdir(parents=True)
    data = {"profiles": [{"id": 1, "name": "Main"}]}
    (profiles2 / "profiles.json").write_text(json.dumps(data), encoding="utf-8")
    (profiles2 / "Main-1.properties").write_text("key=value", encoding="utf-8")
    return profiles2


def test_backup_creates_copy(tmp_path):
    profiles2 = _make_profiles2(tmp_path)

    backup_dir = create_backup(profiles2)

    assert backup_dir.is_dir()
    assert (backup_dir / "profiles.json").is_file()
    assert (backup_dir / "Main-1.properties").is_file()


def test_backup_folder_name_format(tmp_path):
    profiles2 = _make_profiles2(tmp_path)
    fake_now = datetime(2026, 3, 22, 14, 30, 45)

    with patch("src.core.backup.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.strftime = datetime.strftime
        backup_dir = create_backup(profiles2)

    assert backup_dir.name == "profiles2-backup20260322143045"


def test_backup_is_sibling_of_profiles2(tmp_path):
    profiles2 = _make_profiles2(tmp_path)

    backup_dir = create_backup(profiles2)

    assert backup_dir.parent == profiles2.parent
