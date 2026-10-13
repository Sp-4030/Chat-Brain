"""Lightweight and Robust Language Detection Utility.

Detects language and script of incoming live chat messages:
- Marathi (Devanagari)
- Marathi (Roman script)
- Hindi (Devanagari)
- Hinglish (Roman Hindi)
- English
- Mixed / Unknown
"""

from __future__ import annotations

import re
from typing import Dict, Tuple


class LanguageDetector:
    """Detects likely language of live chat messages using script analysis and lexical cues."""

    # Common Marathi Devanagari words/markers
    MARATHI_DEVANAGARI_MARKERS = {
        "आहे", "आहेत", "आहात", "नाही", "नाहीत", "हो", "काय", "कसा", "कशी", "कसे",
        "कुठे", "कधी", "का", "करणार", "करतो", "करते", "करतोय", "करतेय", "नमस्कार",
        "भाऊ", "दादा", "मित्रा", "सांग", "सांगा", "झालं", "झाला", "झाली", "चा", "ची", "चे", "च्या"
    }

    # Common Hindi Devanagari words/markers
    HINDI_DEVANAGARI_MARKERS = {
        "है", "हैं", "हो", "था", "थी", "थे", "क्या", "कैसे", "कैसा", "कैसी",
        "कहाँ", "कब", "क्यों", "क्यो", "नहीं", "करना", "करता", "करती", "करते",
        "नमस्ते", "भाई", "दोस्त", "बताओ", "बता", "हुआ", "होगी", "होगा", "का", "की", "के"
    }

    # Common Roman Marathi markers
    MARATHI_ROMAN_MARKERS = {
        "kay", "kaay", "kasa", "kashi", "kase", "kas", "kuthe", "kute", "kadhi", "ka",
        "aahe", "ahet", "ahes", "nahi", "nahit", "bhava", "dada", "mitra", "sang", "sanga",
        "zala", "zhala", "zali", "zhali", "zal", "zhalo", "bol", "bola", "karto", "karte",
        "kartoy", "kartey", "kartoes", "kasahes", "kashihes", "kuthla", "kuthli"
    }

    # Common Hinglish (Roman Hindi) markers
    HINGLISH_MARKERS = {
        "kya", "kaise", "kaisa", "kaisi", "kyu", "kyun", "kaha", "kahan", "kab", "kon",
        "kaun", "bhai", "bhaiya", "yaar", "dost", "nahi", "nhi", "haan", "han", "matlab",
        "karo", "karega", "hoga", "hogi", "accha", "achha", "sahi", "mast", "sab", "kuch",
        "batao", "bata", "chal", "raha", "rahe", "rahi", "thik", "theek", "tera", "meri", "mera"
    }

    # Common English markers
    ENGLISH_MARKERS = {
        "the", "is", "are", "was", "were", "what", "how", "why", "where", "when",
        "who", "can", "could", "would", "should", "you", "your", "hello", "hi", "hey",
        "good", "nice", "awesome", "bro", "brother", "friend", "please", "thanks", "thank"
    }

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Strip URLs, mentions, emojis and normalize whitespace."""
        # Remove URLs
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        # Remove mentions
        text = re.sub(r"@\w+", "", text)
        # Remove punctuation for tokenization
        text = re.sub(r"[^\w\s\u0900-\u097F]", " ", text)
        return text.strip().lower()

    @classmethod
    def detect(cls, text: str) -> Tuple[str, float]:
        """Detect language and return (language_code, confidence).

        Possible language codes:
        - 'marathi_devanagari'
        - 'hindi_devanagari'
        - 'marathi_roman'
        - 'hinglish'
        - 'english'
        - 'unknown'
        """
        if not text or not text.strip():
            return "unknown", 0.0

        cleaned = cls.clean_text(text)
        if not cleaned:
            return "unknown", 0.0

        # Check for Devanagari script (\u0900-\u097F)
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", cleaned))
        total_alpha = len(re.findall(r"[a-zA-Z\u0900-\u097F]", cleaned))

        tokens = set(cleaned.split())

        # If Devanagari dominates
        if total_alpha > 0 and (devanagari_chars / total_alpha) > 0.4:
            marathi_score = len(tokens.intersection(cls.MARATHI_DEVANAGARI_MARKERS))
            hindi_score = len(tokens.intersection(cls.HINDI_DEVANAGARI_MARKERS))

            if marathi_score > hindi_score:
                return "marathi_devanagari", 0.85
            elif hindi_score > marathi_score:
                return "hindi_devanagari", 0.85
            else:
                # Default to Hindi if ambiguous Devanagari
                return "hindi_devanagari", 0.60

        # Latin / Roman script token scoring
        scores: Dict[str, int] = {
            "marathi_roman": len(tokens.intersection(cls.MARATHI_ROMAN_MARKERS)),
            "hinglish": len(tokens.intersection(cls.HINGLISH_MARKERS)),
            "english": len(tokens.intersection(cls.ENGLISH_MARKERS)),
        }

        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]

        if best_score > 0:
            confidence = min(1.0, 0.5 + (best_score * 0.15))
            return best_lang, confidence

        # Single word or slang fallback heuristics
        if any(w in cleaned for w in ["bhava", "dada", "kay", "aahe"]):
            return "marathi_roman", 0.5
        if any(w in cleaned for w in ["bhai", "yaar", "kya", "kaise"]):
            return "hinglish", 0.5

        # If pure latin words, fallback to English
        latin_words = [w for w in cleaned.split() if w.isalpha()]
        if latin_words:
            return "english", 0.4

        return "unknown", 0.0


def detect_language(text: str) -> str:
    """Convenience helper returning the detected language label."""
    lang, _ = LanguageDetector.detect(text)
    return lang
