"""Gmail API client: authenticate and fetch transaction notification emails."""

import base64
import re
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
_CONFIG_DIR = Path.home() / ".config" / "spendstream"
_TOKEN_PATH = _CONFIG_DIR / "token.json"
_CREDENTIALS_PATH = _CONFIG_DIR / "credentials.json"


def get_service() -> Any:
    """Return an authenticated Gmail API service object.

    On first run, opens a browser for OAuth2 consent.
    Token is cached at ~/.config/spendstream/token.json.
    Place credentials.json (from Google Cloud Console) at
    ~/.config/spendstream/credentials.json before first run.
    """
    creds: Credentials | None = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _TOKEN_PATH.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_emails(service: Any, label: str, max_results: int = 100) -> list[dict[str, Any]]:
    """Return full message dicts for emails matching the given Gmail label."""
    result = (
        service.users()
        .messages()
        .list(userId="me", q=f"label:{label}", maxResults=max_results)
        .execute()
    )
    messages: list[dict[str, Any]] = result.get("messages", [])
    return [
        service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        for msg in messages
    ]


def get_header(message: dict[str, Any], name: str) -> str:
    """Return the value of a header field from a full Gmail message dict."""
    headers: list[dict[str, str]] = message.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def get_body(message: dict[str, Any]) -> str:
    """Return the decoded text body of a Gmail message.

    Prefers text/plain; falls back to text/html with tags stripped.
    Recurses through multipart MIME trees.
    """

    def _find(payload: dict[str, Any], mime: str) -> str | None:
        if payload.get("mimeType") == mime:
            data: str = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            found = _find(part, mime)
            if found:
                return found
        return None

    payload: dict[str, Any] = message.get("payload", {})
    text = _find(payload, "text/plain")
    if text:
        return text
    html = _find(payload, "text/html")
    if html:
        return _strip_html(html)
    return ""


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    for entity, char in {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&nbsp;": " ",
        "&#39;": "'",
        "&quot;": '"',
    }.items():
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()
