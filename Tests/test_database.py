"""Test DB layer using mongomock (if installed) or real URI skip."""
import pytest

try:
    import mongomock
    HAVE_MOCK = True
except ImportError:
    HAVE_MOCK = False


@pytest.mark.skipif(not HAVE_MOCK, reason="mongomock not installed")
def test_user_creation_and_isolation(monkeypatch, mock_settings):
    from pymongo import MongoClient
    # Patch _db in mongodb module
    import Database.mongodb as mdb
    client = mongomock.MongoClient()
    monkeypatch.setattr(mdb, "_client", client)
    monkeypatch.setattr(mdb, "_db", client["test_db"])

    from Database.indexes import ensure_indexes
    from Database.repositories import UserRepository, SettingsRepository

    ensure_indexes()
    u1 = UserRepository().get_or_create(111, "alice")
    u2 = UserRepository().get_or_create(222, "bob")
    assert u1["telegram_user_id"] == 111
    assert u2["telegram_user_id"] == 222

    SettingsRepository().update(111, {"default_pages": 42})
    s1 = SettingsRepository().get(111)
    s2 = SettingsRepository().get(222)
    assert s1["default_pages"] == 42
    assert s2["default_pages"] == 20  # untouched default


@pytest.mark.skipif(not HAVE_MOCK, reason="mongomock not installed")
def test_settings_persistence(monkeypatch):
    import Database.mongodb as mdb
    from pymongo import MongoClient
    client = mongomock.MongoClient()
    monkeypatch.setattr(mdb, "_db", client["test_db"])

    from Database.repositories import SettingsRepository
    SettingsRepository().update(999, {"art_style": "Minimalist", "default_pages": 15})
    # Simulate restart: fresh read
    s = SettingsRepository().get(999)
    assert s["art_style"] == "Minimalist"
    assert s["default_pages"] == 15