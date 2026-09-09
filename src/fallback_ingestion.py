"""
Secondary ingestion paths — Demo Mode and file upload. Gmail (src/gmail_auth.py)
is the primary, star workflow; these exist so the app is explorable even
before Gmail is connected.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "spam_dataset.csv"

SCHEMA_COLUMNS = [
    "message_id", "thread_id", "sender", "recipient",
    "subject", "date", "body", "labels", "source",
]

DEMO_SPAM_SENDERS = [
    "rewards@promo-alerts.com", "no-reply@claim-now.biz", "billing@secure-update.net",
    "winner@lucky-draw.info", "support@account-verify.cc", "deals@mega-savings.top",
]
DEMO_HAM_SENDERS = [
    "professor@university.edu", "manager@company.com", "hr@company.com",
    "friend@gmail.com", "billing@yourbank.com", "team@project.org",
]
DEMO_SPAM_SUBJECTS = [
    "Claim your reward now", "You have WON a prize!!!", "Urgent: verify your account",
    "Limited time cash offer", "Your package is waiting", "Free gift inside",
]
DEMO_HAM_SUBJECTS = [
    "Project meeting tomorrow", "Q3 budget review", "Re: lunch plans",
    "Weekly team sync notes", "Invoice for last month", "Notes from today's call",
]


def load_demo_emails(n: int = 40, spam_ratio: float = 0.35, seed: int | None = None) -> pd.DataFrame:
    rng = random.Random(seed)
    raw = pd.read_csv(DATA_PATH)
    n_spam = max(1, int(n * spam_ratio))
    n_ham = max(1, n - n_spam)

    spam_pool = raw[raw["label"] == "spam"].sample(min(n_spam, (raw["label"] == "spam").sum()), random_state=seed)
    ham_pool = raw[raw["label"] == "ham"].sample(min(n_ham, (raw["label"] == "ham").sum()), random_state=seed)
    sample = pd.concat([spam_pool, ham_pool]).sample(frac=1, random_state=seed).reset_index(drop=True)

    now = datetime.now()
    rows = []
    for i, r in sample.iterrows():
        is_spam = r["label"] == "spam"
        sender = rng.choice(DEMO_SPAM_SENDERS if is_spam else DEMO_HAM_SENDERS)
        subject = rng.choice(DEMO_SPAM_SUBJECTS if is_spam else DEMO_HAM_SUBJECTS)
        rows.append({
            "message_id": f"demo-{i}", "thread_id": f"thread-{i // 3}",
            "sender": sender, "recipient": "you@inbox.com", "subject": subject,
            "date": now - timedelta(minutes=rng.randint(5, 60 * 24 * 4)),
            "body": str(r["text"]), "labels": "INBOX", "source": "demo_dataset",
        })
    return pd.DataFrame(rows).sort_values("date", ascending=False).reset_index(drop=True)


def normalize_dataframe(df: pd.DataFrame, source_label: str = "uploaded") -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    def pick(*candidates, default=""):
        for c in candidates:
            if c in df.columns:
                return df[c].astype(str)
        return pd.Series([default] * len(df))

    out = pd.DataFrame()
    out["message_id"] = [f"{source_label}-{i}" for i in range(len(df))]
    out["thread_id"] = pick("thread_id", "thread", default="")
    out["sender"] = pick("sender", "from", default="unknown@unknown.com")
    out["recipient"] = pick("recipient", "to", default="me@inbox.com")
    out["subject"] = pick("subject", "title", default="(no subject)")
    out["date"] = pick("date", "timestamp", default="")
    out["body"] = pick("body", "text", "message", "content", default="")
    out["labels"] = pick("labels", "label", default="INBOX")
    out["source"] = source_label

    parsed_dates = pd.to_datetime(out["date"], errors="coerce")
    if parsed_dates.isna().all():
        now = datetime.now()
        parsed_dates = pd.Series([now - timedelta(hours=i * 3) for i in range(len(out))])
    out["date"] = parsed_dates
    out = out.dropna(subset=["body"])
    out = out[out["body"].str.strip() != ""]
    return out.reset_index(drop=True)


def load_from_csv(uploaded_file) -> pd.DataFrame:
    return normalize_dataframe(pd.read_csv(uploaded_file), source_label="csv_upload")


def load_from_json(uploaded_file) -> pd.DataFrame:
    return normalize_dataframe(pd.read_json(uploaded_file), source_label="json_upload")
