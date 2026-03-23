"""Tests for src.utils.paths."""

import json

from src.utils.paths import (
    load_profiles_json,
    validate_runelite_folder,
)
import pytest


def _make_profiles2(tmp_path, profiles_list=None):
    """Helper: create a profiles2 dir with profiles.json in the real format."""
    profiles2 = tmp_path / ".runelite" / "profiles2"
    profiles2.mkdir(parents=True)
    if profiles_list is not None:
        data = {"profiles": profiles_list}
        (profiles2 / "profiles.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
    return profiles2


class TestValidateRuneliteFolder:
    def test_valid_folder(self, tmp_path):
        profiles = [{"id": 1, "name": "Test", "sync": False, "rev": -1}]
        _make_profiles2(tmp_path, profiles)
        result = validate_runelite_folder(tmp_path / ".runelite")
        assert result.name == "profiles2"

    def test_missing_profiles2_dir(self, tmp_path):
        with pytest.raises(ValueError, match="profiles2 directory not found"):
            validate_runelite_folder(tmp_path / ".runelite")

    def test_missing_profiles_json(self, tmp_path):
        (tmp_path / ".runelite" / "profiles2").mkdir(parents=True)
        with pytest.raises(ValueError, match="profiles.json not found"):
            validate_runelite_folder(tmp_path / ".runelite")

    def test_malformed_json(self, tmp_path):
        profiles2 = tmp_path / ".runelite" / "profiles2"
        profiles2.mkdir(parents=True)
        (profiles2 / "profiles.json").write_text("{bad json", encoding="utf-8")
        with pytest.raises(ValueError, match="not valid JSON"):
            validate_runelite_folder(tmp_path / ".runelite")

    def test_json_bare_array_rejected(self, tmp_path):
        profiles2 = tmp_path / ".runelite" / "profiles2"
        profiles2.mkdir(parents=True)
        (profiles2 / "profiles.json").write_text('[{"id": 1}]', encoding="utf-8")
        with pytest.raises(ValueError, match="'profiles' key"):
            validate_runelite_folder(tmp_path / ".runelite")

    def test_json_missing_profiles_key(self, tmp_path):
        profiles2 = tmp_path / ".runelite" / "profiles2"
        profiles2.mkdir(parents=True)
        (profiles2 / "profiles.json").write_text('{"other": []}', encoding="utf-8")
        with pytest.raises(ValueError, match="'profiles' key"):
            validate_runelite_folder(tmp_path / ".runelite")


class TestLoadProfilesJson:
    def test_loads_valid_profiles(self, tmp_path):
        profiles = [
            {"id": 1, "name": "Main"},
            {"id": 2, "name": "Alt"},
        ]
        profiles2 = _make_profiles2(tmp_path, profiles)
        result = load_profiles_json(profiles2)
        assert len(result) == 2
        assert result[0]["name"] == "Main"

    def test_skips_entries_with_missing_fields(self, tmp_path):
        profiles = [
            {"id": 1, "name": "Good"},
            {"name": "NoId"},  # missing id
        ]
        profiles2 = _make_profiles2(tmp_path, profiles)
        result = load_profiles_json(profiles2)
        assert len(result) == 1
        assert result[0]["name"] == "Good"

    def test_skips_entries_with_wrong_types(self, tmp_path):
        profiles = [
            {"id": "not-an-int", "name": "Bad"},
        ]
        profiles2 = _make_profiles2(tmp_path, profiles)
        result = load_profiles_json(profiles2)
        assert len(result) == 0

    def test_preserves_extra_fields(self, tmp_path):
        profiles = [
            {"id": 1, "name": "Test", "sync": False, "active": True, "defaultForRsProfiles": []},
        ]
        profiles2 = _make_profiles2(tmp_path, profiles)
        result = load_profiles_json(profiles2)
        assert result[0]["active"] is True
        assert result[0]["defaultForRsProfiles"] == []
