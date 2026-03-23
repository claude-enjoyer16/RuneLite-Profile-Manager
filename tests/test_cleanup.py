"""Tests for src.core.cleanup."""

import json

from src.core.cleanup import find_orphaned_files, delete_orphaned_files


def _make_profiles2(tmp_path, profiles_list, extra_files=None):
    profiles2 = tmp_path / "profiles2"
    profiles2.mkdir()
    data = {"profiles": profiles_list}
    (profiles2 / "profiles.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
    for name in (extra_files or []):
        (profiles2 / name).write_text("data", encoding="utf-8")
    return profiles2


def test_finds_orphaned_properties(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ], extra_files=[
        "wheel-100.properties",
        "old-999.properties",
    ])

    orphaned = find_orphaned_files(profiles2)

    assert len(orphaned) == 1
    assert orphaned[0].name == "old-999.properties"


def test_no_orphans(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ], extra_files=[
        "wheel-100.properties",
    ])

    orphaned = find_orphaned_files(profiles2)

    assert orphaned == []


def test_ignores_non_properties_files(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ], extra_files=[
        "wheel-100.properties",
        "somefile.txt",
    ])

    orphaned = find_orphaned_files(profiles2)

    assert orphaned == []


def test_delete_orphaned_files(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ], extra_files=[
        "wheel-100.properties",
        "old-999.properties",
        "stale-888.properties",
    ])

    orphaned = find_orphaned_files(profiles2)
    assert len(orphaned) == 2

    delete_orphaned_files(orphaned)

    remaining = [f.name for f in profiles2.iterdir() if f.suffix == ".properties"]
    assert remaining == ["wheel-100.properties"]


def test_rsprofile_properties_not_orphaned(tmp_path):
    profiles2 = _make_profiles2(tmp_path, [
        {"id": -1, "name": "$rsprofile", "sync": True, "rev": -1},
        {"id": 100, "name": "wheel", "sync": False, "rev": -1},
    ], extra_files=[
        "$rsprofile--1.properties",
        "wheel-100.properties",
    ])

    orphaned = find_orphaned_files(profiles2)

    assert orphaned == []
