"""Tests for Multilingual Kitchen Interface (Module I: I8)."""

from messwise.i18n import SUPPORTED_LANGUAGES, TRANSLATIONS, get_text


def test_i18n_supported_languages():
    """Verify all declared languages exist in configuration."""
    assert "en" in SUPPORTED_LANGUAGES
    assert "te" in SUPPORTED_LANGUAGES
    assert "hi" in SUPPORTED_LANGUAGES


def test_i18n_known_keys_translation():
    """Verify kitchen keys translate correctly to Telugu and Hindi."""
    # Cooked quantity
    assert "Vandina" in get_text("cooked_qty", "te")
    assert "Bana" in get_text("cooked_qty", "hi")
    assert get_text("cooked_qty", "en") == "Cooked Quantity"

    # Leftover quantity
    assert "Migilindi" in get_text("leftover_qty", "te")
    assert "Bacha" in get_text("leftover_qty", "hi")
    assert get_text("leftover_qty", "en") == "Leftover Quantity"

    # Safety clock
    assert "90" in get_text("safety_clock", "te")
    assert "90" in get_text("safety_clock", "hi")
    assert "90" in get_text("safety_clock", "en")


def test_i18n_fallback_to_english_on_unknown_lang_or_missing_key():
    """Verify unconfigured language or missing key falls back gracefully without exception."""
    # Unknown language falls back to English
    assert get_text("cooked_qty", "fr") == "Cooked Quantity"

    # Unknown key converts snake_case to title
    assert get_text("custom_special_ingredient", "en") == "Custom Special Ingredient"
