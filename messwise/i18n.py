"""MessWise Multilingual Kitchen Translations (Module I: I8).

Centralized translation dictionary providing kitchen-facing labels in English,
Hindi, and Telugu (including transliterations) with automatic fallback to English.
Preserves food-safety integrity: safety rules are never machine-translated arbitrarily.
"""

from typing import Dict

# Available interface languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "te": "తెలుగు (Telugu)",
    "hi": "हिन्दी (Hindi)",
}

# Centralized translation dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "cooked_qty": {
        "en": "Cooked Quantity",
        "te": "వండిన పరిమాణం (Vandina)",
        "hi": "पकाई गई मात्रा (Bana)",
    },
    "leftover_qty": {
        "en": "Leftover Quantity",
        "te": "మిగిలిన పరిమాణం (Migilindi)",
        "hi": "बची हुई मात्रा (Bacha)",
    },
    "headcount": {
        "en": "Student Headcount / Attendance",
        "te": "హాజరైన విద్యార్థుల సంఖ్య (Headcount)",
        "hi": "उपस्थित छात्रों की संख्या (Headcount)",
    },
    "ran_out": {
        "en": "Ran Out Before Meal Ended (Shortage)",
        "te": "భోజనం ముగిసేలోపు అయిపోయింది (Ran Out)",
        "hi": "भोजन समाप्त होने से पहले खत्म हो गया (Ran Out)",
    },
    "dish_name": {
        "en": "Dish Name",
        "te": "వంటకం పేరు",
        "hi": "व्यंजन का नाम",
    },
    "meal_slot": {
        "en": "Meal Slot",
        "te": "భోజన సమయం (Breakfast/Lunch/Snacks/Dinner)",
        "hi": "भोजन का समय (Breakfast/Lunch/Snacks/Dinner)",
    },
    "confirm_save": {
        "en": "Confirm & Save to Kitchen Register",
        "te": "నిర్ధారించి రిజిస్టర్‌లో నమోదు చేయండి (Confirm & Save)",
        "hi": "पुष्टि करें और रजिस्टर में सहेजें (Confirm & Save)",
    },
    "safety_clock": {
        "en": "Safety Clock (90-minute ambient temperature limit)",
        "te": "భద్రతా సమయం (గది ఉష్ణోగ్రత వద్ద 90 నిమిషాల పరిమితి)",
        "hi": "सुरक्षा समय (सामान्य तापमान पर 90 मिनट की सीमा)",
    },
    "quick_voice": {
        "en": "Quick Voice Log",
        "te": "వాయిస్ లాగింగ్ (Voice Entry)",
        "hi": "ध्वनि प्रविष्टि (Voice Entry)",
    },
    "photo_estimate": {
        "en": "Photo Volume Estimate",
        "te": "ఫోటో అంచనా (Photo Estimate)",
        "hi": "फोटो अनुमान (Photo Estimate)",
    },
}


def get_text(key: str, lang: str = "en") -> str:
    """Retrieve translated text with automatic fallback to English."""
    clean_lang = (lang or "en").lower().strip()
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key.replace("_", " ").title()
    return entry.get(clean_lang) or entry.get("en") or key
