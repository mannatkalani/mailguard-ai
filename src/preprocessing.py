"""
Text preprocessing pipeline.

This mirrors, exactly, the cleaning pipeline used in the original research
notebook (spam.ipynb) so that the deployed application stays consistent
with the model that was trained and evaluated there:

    1. lowercase
    2. replace URLs with the literal token "url"
    3. replace email addresses with the literal token "email"
    4. replace digits with the literal token "num"
    5. strip non-alphabetic characters
    6. tokenize on whitespace
    7. remove English stopwords
    8. apply Porter stemming

Any change here should be made in the notebook first, then mirrored here,
so the serialized model artifacts and the live app never drift apart.
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

_NLTK_READY = False


def ensure_nltk_data() -> None:
    """Download the (small) NLTK corpora needed for preprocessing, once."""
    global _NLTK_READY
    if _NLTK_READY:
        return
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    _NLTK_READY = True


ensure_nltk_data()
STOP_WORDS = set(stopwords.words("english"))
STEMMER = PorterStemmer()

URL_RE = re.compile(r"http\S+|www\S+")
EMAIL_RE = re.compile(r"\S+@\S+")
DIGIT_RE = re.compile(r"\d+")
NON_ALPHA_RE = re.compile(r"[^a-z\s]")


def clean_text(text: str) -> str:
    """Apply the full notebook preprocessing pipeline to one message."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = URL_RE.sub(" url ", text)
    text = EMAIL_RE.sub(" email ", text)
    text = DIGIT_RE.sub(" num ", text)
    text = NON_ALPHA_RE.sub(" ", text)
    words = text.split()
    words = [STEMMER.stem(w) for w in words if w not in STOP_WORDS]
    return " ".join(words)


# ---------------------------------------------------------------------------
# Heuristic signal extraction — used ONLY for the explainability / "why was
# this flagged" panel. These are separate from the trained ML model and are
# always labeled as heuristics in the UI, never presented as model output.
# ---------------------------------------------------------------------------

SUSPICIOUS_KEYWORDS = [
    "free", "winner", "won", "prize", "claim", "urgent", "act now", "limited time",
    "click here", "click now", "verify", "account suspended", "congratulations",
    "cash", "credit", "loan", "gift card", "risk free", "guarantee", "viagra",
    "cialis", "pharmacy", "lottery", "million", "wire transfer", "bitcoin",
    "crypto", "password", "unsubscribe", "offer expires", "no obligation",
    "call now", "text stop", "reply stop", "100% free", "double your",
]


def raw_signal_features(text: str) -> dict:
    """Cheap, interpretable surface signals computed on the raw message text."""
    if not isinstance(text, str):
        text = ""
    length = max(len(text), 1)
    n_upper = sum(1 for c in text if c.isupper())
    n_digits = sum(1 for c in text if c.isdigit())
    n_exclaim = text.count("!")
    urls = len(URL_RE.findall(text))
    lowered = text.lower()
    hits = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered]
    return {
        "char_count": len(text),
        "word_count": len(text.split()),
        "upper_ratio": n_upper / length,
        "digit_ratio": n_digits / length,
        "exclaim_count": n_exclaim,
        "url_count": urls,
        "has_url": urls > 0,
        "suspicious_keyword_hits": hits,
        "suspicious_keyword_count": len(hits),
    }
