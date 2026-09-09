"""
Gmail connection, made as easy as possible for the end user.

This uses Google's "installed app" OAuth flow (`InstalledAppFlow.run_local_server`)
instead of a web-redirect flow. Practically, that means:

  - No redirect URI to configure or copy-paste.
  - No Streamlit secrets to manage.
  - Clicking "Connect Gmail" opens the user's default browser straight to
    Google's sign-in screen; after they click Allow, the tab auto-closes
    and control returns to the app.
  - The resulting token is cached in `token.json` next to this project, so
    every subsequent run reconnects instantly with zero clicks — no login,
    no popup — until the person explicitly disconnects or revokes access.

The ONE thing that can't be skipped (Google requires it of every app) is a
one-time setup where the project owner creates an OAuth client in Google
Cloud Console and downloads `credentials.json`. See the README for the
exact steps — it takes about two minutes and is done once, ever.
"""

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent.parent
CREDENTIALS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SCHEMA_COLUMNS = [
    "message_id", "thread_id", "sender", "recipient",
    "subject", "date", "body", "labels", "source",
]


def is_configured() -> bool:
    """Has the one-time Google Cloud OAuth client been set up?"""
    return CREDENTIALS_PATH.exists()


def _load_cached_credentials():
    from google.oauth2.credentials import Credentials

    if not TOKEN_PATH.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception:
        return None


def is_connected() -> bool:
    """True if we have a valid (or refreshable) cached token — no browser needed."""
    creds = _load_cached_credentials()
    if creds is None:
        return False
    if creds.valid:
        return True
    if creds.expired and creds.refresh_token:
        return True
    return False


def get_credentials():
    """Return valid credentials, refreshing the cached token silently if possible.
    Only falls back to opening a browser if there's no usable cached token at all.
    """
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = _load_cached_credentials()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
        return creds

    # No usable token — run the one-click browser consent flow.
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    TOKEN_PATH.write_text(creds.to_json())
    return creds


def disconnect() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


def get_connected_email(creds) -> str:
    from googleapiclient.discovery import build

    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    return profile.get("emailAddress", "unknown")


def fetch_messages(creds, max_results: int = 30) -> pd.DataFrame:
    """Fetch a batch of messages and normalize them onto the internal schema.
    Read-only — nothing is modified, sent, or deleted in the mailbox.
    """
    from googleapiclient.discovery import build

    service = build("gmail", "v1", credentials=creds)
    resp = service.users().messages().list(userId="me", maxResults=max_results).execute()
    message_ids = [m["id"] for m in resp.get("messages", [])]

    rows = []
    for mid in message_ids:
        msg = service.users().messages().get(userId="me", id=mid, format="full").execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        body_text = _extract_body(msg["payload"]) or msg.get("snippet", "")
        rows.append(
            {
                "message_id": msg.get("id", mid),
                "thread_id": msg.get("threadId", ""),
                "sender": headers.get("from", "unknown"),
                "recipient": headers.get("to", ""),
                "subject": headers.get("subject", "(no subject)"),
                "date": headers.get("date", ""),
                "body": body_text,
                "labels": ",".join(msg.get("labelIds", [])),
                "source": "gmail",
            }
        )

    df = pd.DataFrame(rows, columns=SCHEMA_COLUMNS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df.dropna(subset=["body"])
    df = df[df["body"].str.strip() != ""]
    return df.reset_index(drop=True)


def _extract_body(payload) -> str:
    if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text
    return ""
