"""Shared helpers for bank email parsers."""

import email.utils
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_AMOUNT_RE = re.compile(
    r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)"
)

_DATE_RE = re.compile(
    r"(?:"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\.?\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}/\d{1,2}/\d{2,4}"
    r"|\d{4}-\d{2}-\d{2}"
    r")",
    re.IGNORECASE,
)

_DATE_FORMATS = [
    "%B %d, %Y",  # January 15, 2024
    "%B %d %Y",   # January 15 2024
    "%b %d, %Y",  # Jan 15, 2024
    "%b %d %Y",   # Jan 15 2024
    "%b. %d, %Y", # Jan. 15, 2024
    "%m/%d/%Y",   # 01/15/2024
    "%m/%d/%y",   # 01/15/24
    "%Y-%m-%d",   # 2024-01-15
]


def parse_amount(text: str) -> Decimal | None:
    """Extract the first dollar amount from text."""
    m = _AMOUNT_RE.search(text)
    if not m:
        return None
    try:
        return Decimal(m.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def parse_date(text: str) -> datetime | None:
    """Extract the first recognisable date from text."""
    m = _DATE_RE.search(text)
    if not m:
        return None
    raw = re.sub(r",\s*$", "", m.group(0).strip())
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_email_date(message: dict[str, Any]) -> datetime:
    """Parse the RFC 2822 Date header; falls back to utcnow."""
    from spendstream.gmail import get_header

    date_str = get_header(message, "Date")
    try:
        return email.utils.parsedate_to_datetime(date_str).replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()
