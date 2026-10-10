"""MessWise Multilingual Voice Logging & Parser (Module C: C5).

Implements specifications from PLAN.md Section 5 (Module C5), Section 9.1, and Section 10:
- Multilingual speech capture: English, Hindi, and Telugu (transliterated).
- Domain-specific dish synonym matching (e.g. annam / chawal / rice, pappu / dal, perugu / curd).
- Number word normalization (digits, English words, Hindi/Telugu transliterated numbers).
- Role-aware quantity assignment: distinguishes cooked quantities from leftover quantities
  using semantic language cues rather than blindly picking the first two numbers.
- Pre-filled form review: kitchen staff must review and explicitly confirm before any database write.
- Audio privacy: temporary audio is processed in-memory and discarded. No biometric data collected.
"""

from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Optional SpeechRecognition import with graceful fallback
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    sr = None
    HAS_SPEECH_RECOGNITION = False

from messwise.validation import normalize_unit


# Dish Synonym Dictionary (maps variations across English, Hindi, Telugu to catalog names)
DISH_SYNONYMS: Dict[str, str] = {
    # Rice / Grains
    "rice": "Rice",
    "steamed rice": "Rice",
    "white rice": "Rice",
    "chawal": "Rice",
    "chaawal": "Rice",
    "bhat": "Rice",
    "annam": "Rice",
    "annamu": "Rice",

    # Dal / Lentils
    "dal": "Dal Tadka",
    "daal": "Dal Tadka",
    "dal tadka": "Dal Tadka",
    "pappu": "Dal Tadka",
    "sambar": "Dal Tadka",
    "saaru": "Dal Tadka",
    "chaaru": "Dal Tadka",
    "rasam": "Dal Tadka",

    # Roti / Breads
    "roti": "Roti",
    "rotis": "Roti",
    "chapati": "Roti",
    "chapathi": "Roti",
    "chapatis": "Roti",
    "phulka": "Roti",
    "poori": "Roti",
    "puri": "Roti",
    "rotlu": "Roti",

    # Curd / Yogurt / Raita
    "curd": "Curd",
    "dahi": "Curd",
    "perugu": "Curd",
    "raita": "Curd",

    # Curries / Sabzi
    "curry": "Veg Curry",
    "sabzi": "Veg Curry",
    "sabji": "Veg Curry",
    "kura": "Veg Curry",
    "koora": "Veg Curry",
    "aloo sabzi": "Veg Curry",
    "paneer": "Paneer Butter Masala",
    "paneer curry": "Paneer Butter Masala",
}

# Number words mapping across English, Hindi, and Telugu transliteration
NUMBER_WORDS: Dict[str, float] = {
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "twenty-five": 25, "thirty": 30,
    "thirty-five": 35, "forty": 40, "forty-five": 45, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
    "ninety": 90, "hundred": 100,

    # Hindi transliteration
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5, "che": 6, "chheh": 6, "chhah": 6,
    "saat": 7, "aath": 8, "ath": 8, "nau": 9, "das": 10, "gyarah": 11, "baarah": 12, "terah": 13, "chaudah": 14,
    "pandrah": 15, "solah": 16, "satrah": 17, "athaarah": 18, "unnees": 19, "bees": 20, "pachees": 25, "tees": 30,
    "chaalis": 40, "chalis": 40, "pachaas": 50, "pachas": 50, "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
    "sau": 100,

    # Telugu transliteration
    "okati": 1, "rendu": 2, "moodu": 3, "naalugu": 4, "nalugu": 4, "aidu": 5, "aaru": 6, "yedu": 7, "enimidi": 8,
    "tommidi": 9, "padi": 10, "padakondu": 11, "pannerendu": 12, "padamoodu": 13, "padanaalugu": 14, "padihenu": 15,
    "padahaaru": 16, "padihedu": 17, "paddenimidi": 18, "pantommidi": 19, "iravai": 20, "iravai aidu": 25, "muppai": 30,
    "nalabhai": 40, "nalabai": 40, "yaabhai": 50, "yabai": 50, "aravai": 60, "debbai": 70, "enabhai": 80, "tombhai": 90,
    "vanda": 100,
}

# Semantic role keywords
COOKED_CUES = {
    # English
    "cooked", "cook", "made", "prepared", "prepare", "make",
    # Hindi
    "bana", "banaya", "pakaya", "taiyar", "banaye",
    # Telugu
    "vandamu", "vandindi", "vandaru", "chesamu", "tayaru chesamu", "vandam",
}

LEFTOVER_CUES = {
    # English
    "left", "leftover", "leftovers", "remaining", "remained", "balance", "remain", "remains",
    # Hindi
    "bacha", "bach gaya", "bache", "shesh", "bachi",
    # Telugu
    "migilindi", "migilina", "migilipoyindi", "unindi", "migilindhi", "migilipoyindhi",
}

RAN_OUT_CUES = {
    # English
    "ran out", "run out", "finished", "empty", "zero left",
    # Hindi
    "khatam", "khatam ho gaya", "khatam hogaya",
    # Telugu
    "aipoindi", "ayipoyindi", "chalaledu", "aipoyindhi",
}


@dataclass
class VoiceParseResult:
    """Structured output from parsing a kitchen logging speech utterance."""

    raw_transcript: str
    detected_language: str
    dish_name: Optional[str]
    cooked_qty: Optional[float]
    cooked_unit: Optional[str]
    leftover_qty: Optional[float]
    leftover_unit: Optional[str]
    ran_out: bool
    confidence_status: str  # "high", "moderate", "low", "failed"
    explanation: str
    unrecognized_tokens: List[str] = field(default_factory=list)
    is_valid_for_review: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_token_text(text: str) -> str:
    """Clean punctuation and normalize whitespace while preserving alphanumeric words."""
    cleaned = re.sub(r"[^\w\s\.-]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def extract_numeric_value(token: str) -> Optional[float]:
    """Parse integer, float, or number word into a float value."""
    clean = token.strip().lower()
    # Direct numeric digits
    try:
        return float(clean)
    except ValueError:
        pass

    # Number words dictionary lookup
    if clean in NUMBER_WORDS:
        return NUMBER_WORDS[clean]

    return None


def match_unit_expression(word: str) -> Optional[str]:
    """Map token to canonical MessWise unit (kg, L, count)."""
    w = word.strip().lower()
    if w in ("kg", "kgs", "kilo", "kilos", "kilolu", "kilogram", "kilograms"):
        return "kg"
    if w in ("l", "liter", "liters", "litre", "litres", "leeter"):
        return "L"
    if w in ("count", "nos", "pieces", "rotis", "units", "items"):
        return "count"
    return None


def parse_voice_utterance(
    transcript: str,
    dish_catalog: Optional[List[str]] = None,
    language_hint: str = "auto",
) -> VoiceParseResult:
    """Parse a kitchen measurement speech transcript into structured quantities (C5).

    Distinguishes cooked vs leftover measurements using semantic cues.
    Does NOT assume the first number is cooked and second is leftover.
    """
    clean_text = normalize_token_text(transcript)
    if not clean_text:
        return VoiceParseResult(
            raw_transcript=transcript,
            detected_language=language_hint,
            dish_name=None,
            cooked_qty=None,
            cooked_unit=None,
            leftover_qty=None,
            leftover_unit=None,
            ran_out=False,
            confidence_status="failed",
            explanation="Empty transcript provided.",
            is_valid_for_review=False,
        )

    # 1. Identify Dish
    detected_dish: Optional[str] = None
    detected_lang: str = language_hint

    # Check known dish catalog first if supplied
    if dish_catalog:
        for d in dish_catalog:
            d_norm = normalize_token_text(d)
            if re.search(rf"\b{re.escape(d_norm)}\b", clean_text):
                detected_dish = d
                break

    # Check synonym dictionary
    if not detected_dish:
        # Match multi-word synonyms first, then single words
        sorted_synonyms = sorted(DISH_SYNONYMS.keys(), key=lambda s: len(s), reverse=True)
        for syn in sorted_synonyms:
            if re.search(rf"\b{re.escape(syn)}\b", clean_text):
                detected_dish = DISH_SYNONYMS[syn]
                # Language detection heuristics
                if syn in ("chawal", "dahi", "sabzi", "sabji"):
                    detected_lang = "Hindi"
                elif syn in ("annam", "annamu", "pappu", "perugu", "kura", "koora"):
                    detected_lang = "Telugu"
                elif syn in ("rice", "curd", "curry"):
                    detected_lang = "English"
                break

    # 2. Detect Ran Out cue
    ran_out = False
    for cue in RAN_OUT_CUES:
        if cue in clean_text:
            ran_out = True
            break

    # 3. Clause-aware Quantity Extraction
    # Split raw transcript into clauses before stripping punctuation
    raw_clauses = re.split(r"[,;]|\band\b|\baur\b|\bmariyu\b", transcript, flags=re.IGNORECASE)
    clauses = [normalize_token_text(c) for c in raw_clauses if normalize_token_text(c)]
    if len(clauses) == 1:
        # Check if leftover cue appears mid-sentence (e.g. "rice cooked 40 kg left 6 kg")
        for cue in LEFTOVER_CUES:
            if f" {cue}" in clauses[0]:
                parts = clauses[0].split(f" {cue}", 1)
                clauses = [parts[0].strip(), f"{cue} {parts[1]}".strip()]
                break

    cooked_qty: Optional[float] = None
    cooked_unit: Optional[str] = None
    leftover_qty: Optional[float] = None
    leftover_unit: Optional[str] = None
    explanation_parts: List[str] = []
    has_any_cue = False

    def extract_from_clause(clause_text: str) -> List[Tuple[float, str]]:
        c_tokens = clause_text.split()
        m_tokens = []
        k = 0
        while k < len(c_tokens):
            if k + 1 < len(c_tokens):
                pair = f"{c_tokens[k]} {c_tokens[k+1]}"
                if pair in NUMBER_WORDS:
                    m_tokens.append(pair)
                    k += 2
                    continue
            m_tokens.append(c_tokens[k])
            k += 1

        results = []
        for m_idx, tok in enumerate(m_tokens):
            num = extract_numeric_value(tok)
            if num is not None:
                u = "kg"
                if m_idx + 1 < len(m_tokens):
                    u_cand = match_unit_expression(m_tokens[m_idx + 1])
                    if u_cand:
                        u = u_cand
                results.append((num, u))
        return results

    # Process each clause and map based on role cues
    for clause in clauses:
        c_quantities = extract_from_clause(clause)
        if not c_quantities:
            continue

        c_toks = clause.split()
        has_cooked = any(cue in c_toks or any(tok.startswith(cue) for tok in c_toks) for cue in COOKED_CUES)
        has_leftover = any(cue in c_toks or any(tok.startswith(cue) for tok in c_toks) for cue in LEFTOVER_CUES)
        if has_cooked or has_leftover:
            has_any_cue = True

        if has_cooked and not has_leftover and cooked_qty is None:
            cooked_qty, cooked_unit = c_quantities[0]
            if len(c_quantities) > 1 and leftover_qty is None:
                leftover_qty, leftover_unit = c_quantities[1]
        elif has_leftover and not has_cooked and leftover_qty is None:
            leftover_qty, leftover_unit = c_quantities[0]
        elif has_cooked and has_leftover:
            # Both cues inside same clause
            if cooked_qty is None:
                cooked_qty, cooked_unit = c_quantities[0]
            if len(c_quantities) > 1 and leftover_qty is None:
                leftover_qty, leftover_unit = c_quantities[1]
        else:
            # Clause without explicit cue - assign to whichever slot is empty
            if cooked_qty is None:
                cooked_qty, cooked_unit = c_quantities[0]
            elif leftover_qty is None:
                leftover_qty, leftover_unit = c_quantities[0]

    # Fallback if no clause splitting resolved quantities
    if cooked_qty is None and leftover_qty is None:
        all_q = extract_from_clause(clean_text)
        if len(all_q) >= 2:
            cooked_qty, cooked_unit = all_q[0]
            leftover_qty, leftover_unit = all_q[1]
        elif len(all_q) == 1:
            cooked_qty, cooked_unit = all_q[0]
            if ran_out:
                leftover_qty = 0.0
                leftover_unit = cooked_unit
    elif leftover_qty is None and ran_out and cooked_qty is not None:
        leftover_qty = 0.0
        leftover_unit = cooked_unit or "kg"
    elif leftover_qty is None and cooked_qty is not None:
        explanation_parts.append("Detected cooked quantity only; leftover quantity pending measurement.")
    elif cooked_qty is None and leftover_qty is None:
        explanation_parts.append("No numeric quantities detected in utterance.")

    if not has_any_cue and cooked_qty is not None and leftover_qty is not None:
        explanation_parts.append("No explicit cooked/leftover cue words detected; assigned sequentially. Please verify roles.")


    # 4. Data Quality & Sanity Validations
    confidence = "high"
    is_valid = True

    if not detected_dish:
        confidence = "moderate" if (cooked_qty is not None) else "low"
        explanation_parts.append("Dish name could not be identified automatically; please select dish from menu.")

    if cooked_qty is not None and leftover_qty is not None:
        if leftover_qty > cooked_qty:
            confidence = "failed"
            is_valid = False
            explanation_parts.append(
                f"Validation Error: Leftover quantity ({leftover_qty}) cannot be greater than cooked quantity ({cooked_qty})."
            )

    if cooked_qty is None and leftover_qty is None:
        confidence = "failed"
        is_valid = False

    return VoiceParseResult(
        raw_transcript=transcript,
        detected_language=detected_lang if detected_lang != "auto" else "English",
        dish_name=detected_dish,
        cooked_qty=cooked_qty,
        cooked_unit=cooked_unit,
        leftover_qty=leftover_qty,
        leftover_unit=leftover_unit,
        ran_out=ran_out,
        confidence_status=confidence,
        explanation=" ".join(explanation_parts) or "Successfully parsed utterance.",
        unrecognized_tokens=[],
        is_valid_for_review=is_valid,
    )


class AudioTranscriber:
    """Modular speech-to-text adapter with error handling and audio privacy protections."""

    def __init__(self):
        self.is_available = HAS_SPEECH_RECOGNITION
        self.recognizer = sr.Recognizer() if HAS_SPEECH_RECOGNITION else None

    def get_backend_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the speech-to-text backend."""
        return {
            "is_available": self.is_available,
            "engine": "SpeechRecognition (Google Speech API adapter with in-memory WAV capture)",
            "supported_languages": ["en-IN", "hi-IN", "te-IN"],
            "privacy_mode": "Zero persistent audio storage (in-memory processing only)",
            "message": (
                "Transcription backend configured and ready for audio input."
                if self.is_available
                else "Speech recognition backend unavailable. Please install SpeechRecognition or use manual text entry."
            ),
        }

    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        language: str = "en-IN",
    ) -> Tuple[bool, str, Optional[str]]:
        """Transcribe audio bytes (WAV/FLAC) in-memory without persisting raw audio.

        Returns (success, transcript_text, error_message).
        """
        if not self.is_available or self.recognizer is None:
            return (
                False,
                "",
                "Speech recognition backend is not available. Please install SpeechRecognition or enter measurements manually.",
            )

        if not audio_bytes or len(audio_bytes) < 44:  # WAV header minimum length
            return False, "", "Audio recording is empty or shorter than minimum WAV header length."

        try:
            audio_io = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_io) as source:
                # Capture audio data
                audio_data = self.recognizer.record(source)

            # Recognize using Google Speech API (free, built-in adapter to SpeechRecognition)
            transcript = self.recognizer.recognize_google(audio_data, language=language)
            return True, str(transcript).strip(), None

        except sr.UnknownValueError:
            return False, "", "Speech could not be understood from audio. Please speak clearly closer to microphone, or enter manually."
        except sr.RequestError as e:
            return False, "", f"Speech recognition service request error: {str(e)}. Manual entry fallback active."
        except ValueError as e:
            return False, "", f"Audio format error: {str(e)}. Please ensure standard audio recording or enter manually."
        except Exception as e:
            return False, "", f"Audio processing error: {str(e)}. Manual entry fallback active."
