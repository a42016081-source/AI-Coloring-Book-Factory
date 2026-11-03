from Database.models import validate_settings, default_settings


def test_validate_clamps_pages():
    s = validate_settings({"default_pages": 1000})
    assert s["default_pages"] == 200
    s = validate_settings({"default_pages": 0})
    assert s["default_pages"] == 1


def test_validate_rejects_bad_size():
    s = validate_settings({"book_size": "letter"})
    assert s["book_size"] == "8.5x11"


def test_defaults_exist():
    d = default_settings()
    assert d["black_white"] is True
    assert d["ai_provider"] == "pollinations"