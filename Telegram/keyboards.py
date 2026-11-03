"""All ReplyKeyboardMarkup builders."""
from telegram import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📚 Create New Book")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("📖 My Books")],
        [KeyboardButton("🎨 Generate Cover"), KeyboardButton("👁 Preview")],
        [KeyboardButton("📊 Book Status"), KeyboardButton("📦 Download ZIP")],
        [KeyboardButton("🤖 AI Provider"), KeyboardButton("❓ Help")],
    ], resize_keyboard=True, is_persistent=True)


def settings_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📄 Number of Pages"), KeyboardButton("📐 Book Size")],
        [KeyboardButton("🎯 Target Age"), KeyboardButton("🎨 Art Style")],
        [KeyboardButton("🖤 Black & White"), KeyboardButton("🖼 Border Settings")],
        [KeyboardButton("🌐 Language"), KeyboardButton("📚 Book Type")],
        [KeyboardButton("⚙️ Advanced Settings")],
        [KeyboardButton("💾 Save Settings")],
        [KeyboardButton("🔙 Main Menu")],
    ], resize_keyboard=True)


def book_creation_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🐼 Animals"), KeyboardButton("🦖 Dinosaurs")],
        [KeyboardButton("🐱 Cute Cats"), KeyboardButton("🐶 Cute Dogs")],
        [KeyboardButton("🌸 Mandala"), KeyboardButton("🚗 Vehicles")],
        [KeyboardButton("🌳 Nature"), KeyboardButton("✏️ Custom Topic")],
        [KeyboardButton("🔙 Main Menu")],
    ], resize_keyboard=True)


def ai_provider_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Hugging Face")],
        [KeyboardButton("Pollinations")],
        [KeyboardButton("Gemini")],
        [KeyboardButton("Custom API")],
        [KeyboardButton("🔄 Auto Select")],
        [KeyboardButton("🔙 Main Menu")],
    ], resize_keyboard=True)


def download_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📕 Interior PDF"), KeyboardButton("🎨 Front Cover")],
        [KeyboardButton("📘 Back Cover"), KeyboardButton("🖼 Full Wrap Cover")],
        [KeyboardButton("👁 Preview"), KeyboardButton("📦 Complete ZIP")],
        [KeyboardButton("🔙 Main Menu")],
    ], resize_keyboard=True)


def book_management_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📚 All Books")],
        [KeyboardButton("🔄 Retry Failed Book")],
        [KeyboardButton("🗑 Delete Book")],
        [KeyboardButton("📥 Download Previous Book")],
        [KeyboardButton("🔙 Main Menu")],
    ], resize_keyboard=True)


def advanced_settings_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📝 Custom Prompts"), KeyboardButton("🔢 Image Quality")],
        [KeyboardButton("🔁 Regenerate Failed Images"), KeyboardButton("📏 Margins")],
        [KeyboardButton("📃 Paper Type"), KeyboardButton("🎨 Cover Style")],
        [KeyboardButton("🔙 Main Menu")],
    ], resize_keyboard=True)


def cancel_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("❌ Cancel")],
    ], resize_keyboard=True, is_persistent=True)