"""Tests for src.core.profiles."""

import json

from src.core.profiles import load_profiles, delete_profile, duplicate_profile, rename_profile, _next_copy_name


def _make_profiles2(tmp_path, profiles_list):
    """Create a profiles2 dir with profiles.json and return the path."""
    profiles2 = tmp_path / "profiles2"
    profiles2.mkdir()
    data = {"profiles": profiles_list}
    (profiles2 / "profiles.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    return profiles2


def _read_profiles_json(profiles2):
    raw = json.loads((profiles2 / "profiles.json").read_text(encoding="utf-8"))
    return raw["profiles"]


# -- load_profiles --

def test_load_profiles(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
        {"id": 1, "name": "Main", "sync": False, "rev": -1},
        {"id": 2, "name": "Alt", "sync": False, "rev": -1},
    ])
    result = load_profiles(profiles2)
    assert len(result) == 2
    assert result[0]["name"] == "Main"


def test_load_profiles_filters_rsprofile(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
    ])
    result = load_profiles(profiles2)
    assert len(result) == 0


# -- delete_profile --

def test_delete_removes_json_entry(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
        {"id": 100, "name": "Main", "sync": False, "rev": -1},
        {"id": 200, "name": "Alt", "sync": False, "rev": -1},
    ])

    delete_profile(profiles2, {"id": 100, "name": "Main"})

    entries = _read_profiles_json(profiles2)
    ids = [e["id"] for e in entries]
    assert 100 not in ids
    assert -1 in ids
    assert 200 in ids


def test_delete_preserves_other_profiles(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
        {"id": 100, "name": "Main", "sync": False, "rev": -1},
        {"id": 200, "name": "Alt", "sync": False, "rev": -1},
        {"id": 300, "name": "PKing", "sync": False, "rev": -1},
    ])

    delete_profile(profiles2, {"id": 200, "name": "Alt"})

    entries = _read_profiles_json(profiles2)
    remaining_ids = [e["id"] for e in entries]
    assert remaining_ids == [-1, 100, 300]


# -- _next_copy_name --

def test_next_copy_name_basic():
    assert _next_copy_name("wheel", set()) == "wheel (1)"


def test_next_copy_name_increments():
    existing = {"wheel (1)", "wheel (2)"}
    assert _next_copy_name("wheel", existing) == "wheel (3)"


def test_next_copy_name_from_existing_copy():
    existing = {"wheel (1)"}
    assert _next_copy_name("wheel (1)", existing) == "wheel (2)"


def test_next_copy_name_fills_gaps():
    existing = {"wheel (1)", "wheel (3)"}
    assert _next_copy_name("wheel", existing) == "wheel (2)"


# -- duplicate_profile --

def test_duplicate_creates_new_entry(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ])
    (profiles2 / "wheel-100.properties").write_text("key=value", encoding="utf-8")

    new = duplicate_profile(profiles2, {"id": 100, "name": "wheel"})

    assert new["name"] == "wheel (1)"
    assert new["sync"] is False
    assert new["active"] is False
    assert new["rev"] == -1
    assert new["defaultForRsProfiles"] == []

    entries = _read_profiles_json(profiles2)
    assert len(entries) == 3


def test_duplicate_copies_properties_file(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ])
    (profiles2 / "wheel-100.properties").write_text("key=value", encoding="utf-8")

    new = duplicate_profile(profiles2, {"id": 100, "name": "wheel"})

    dst = profiles2 / f"{new['name']}-{new['id']}.properties"
    assert dst.is_file()
    assert dst.read_text(encoding="utf-8") == "key=value"


def test_duplicate_works_without_properties_file(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ])

    new = duplicate_profile(profiles2, {"id": 100, "name": "wheel"})

    assert new["name"] == "wheel (1)"
    entries = _read_profiles_json(profiles2)
    assert len(entries) == 2


def test_duplicate_increments_name(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
        {"id": 200, "name": "wheel (1)", "sync": False, "rev": -1},
    ])

    new = duplicate_profile(profiles2, {"id": 100, "name": "wheel"})

    assert new["name"] == "wheel (2)"


# -- rename_profile --

def test_rename_updates_json(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
        {"id": 100, "name": "Main", "sync": False, "rev": -1},
    ])

    rename_profile(profiles2, {"id": 100, "name": "Main"}, "PKing")

    entries = _read_profiles_json(profiles2)
    renamed = next(e for e in entries if e["id"] == 100)
    assert renamed["name"] == "PKing"


def test_rename_moves_properties_file(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "Main", "sync": False, "rev": -1},
    ])
    (profiles2 / "Main-100.properties").write_text("key=value", encoding="utf-8")

    rename_profile(profiles2, {"id": 100, "name": "Main"}, "PKing")

    assert not (profiles2 / "Main-100.properties").exists()
    assert (profiles2 / "PKing-100.properties").is_file()
    assert (profiles2 / "PKing-100.properties").read_text(encoding="utf-8") == "key=value"


def test_rename_works_without_properties_file(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "Main", "sync": False, "rev": -1},
    ])

    rename_profile(profiles2, {"id": 100, "name": "Main"}, "PKing")

    entries = _read_profiles_json(profiles2)
    renamed = next(e for e in entries if e["id"] == 100)
    assert renamed["name"] == "PKing"
