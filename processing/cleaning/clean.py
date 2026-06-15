"""
cleaner.py
──────────
Utilitas clean text sebelum masuk NLP pipeline.
"""

import re
import html
import unicodedata



CONTENT_PATTERNS = [
    
    r"(?i)(<[^>]+>\s?)*oleh\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*sumber\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*baca\sjuga\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*penulis\s?:[^>]+>",

    
    r"(?i)(<[^>]+>\s?)*source\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*author\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*written\sby\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*read\salso\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*editor\s?:[^>]+>",
    r"(?i)(<[^>]+>\s?)*reporter\s?:[^>]+>",

    
    r"\s?(\(|\[)[^(\)|\])]+(\)|\])\.?(\s?<[^>]+>)*$",

    
    r"^([(<\/?p>|<br \/>)]+)?([^ ]+[ ]?){1,6}[\|\ó\ñ\—\-\–\~\:]",
]


def clean_text(text: str) -> str:
    if not text:
        return ""

    
    text = html.unescape(text)

    
    text = unicodedata.normalize("NFKC", text)

    
    text = text.lower()

    
    for pattern in CONTENT_PATTERNS:
        text = re.sub(pattern, " ", text)

    
    text = re.sub(r"<[^>]+>", " ", text)

    
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    
    text = re.sub(r"\S+@\S+", " ", text)

    
    text = re.sub(r"[@#]\w+", " ", text)

    
    text = re.sub(r"\+?\d[\d\s\-]{7,}\d", " ", text)

    
    text = re.sub(r"\b\d{5,}\b", " ", text)

    
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)

    
    text = re.sub(r"([.!?])\1+", r"\1", text)

    
    text = re.sub(r"(.)\1{4,}", r"\1", text)

    
    text = re.sub(r"[^a-zA-Z0-9\s.,!?%\-]", " ", text)

    
    text = re.sub(r"\s+", " ", text).strip()

    return text