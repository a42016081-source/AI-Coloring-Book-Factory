def test_keyboards_build():
    from Telegram.keyboards import main_menu, settings_menu, book_creation_menu
    mk = main_menu()
    flat = [btn.text for row in mk.keyboard for btn in row]
    assert "📚 Create New Book" in flat
    assert "⚙️ Settings" in flat

    sm = settings_menu()
    flat = [btn.text for row in sm.keyboard for btn in row]
    assert "📄 Number of Pages" in flat
    assert "💾 Save Settings" in flat

    bm = book_creation_menu()
    flat = [btn.text for row in bm.keyboard for btn in row]
    assert "🐼 Animals" in flat
    assert "✏️ Custom Topic" in flat