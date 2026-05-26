"""Parser for Chase transaction alert emails."""

import re
from typing import Any

from spendstream.gmail import get_body, get_header
from spendstream.models import CardIssuer, Transaction
from spendstream.parsers._utils import parse_amount, parse_date, parse_email_date

_SENDER_RE = re.compile(r"@chase\.com", re.IGNORECASE)

# Subject: "Your $42.50 transaction with Whole Foods Market"
_SUBJECT_RE = re.compile(
    r"Your\s+\$[\d,\.]+\s+transaction\s+with\s+(.+)",
    re.IGNORECASE,
)
# Body: "You made a $42.50 transaction with Whole Foods Market on Jan 15 at ..."
_BODY_RE = re.compile(
    r"You\s+made\s+a\s+\$[\d,\.]+\s+transaction\s+with\s+(.+?)\s+on\s+",
    re.IGNORECASE,
)
# Fallback: "transaction with MERCHANT"
_WITH_RE = re.compile(
    r"transaction\s+with\s+([A-Z][^\n\r$]{2,60}?)(?:\s+on\s+|\s*\.|$)",
    re.IGNORECASE,
)


def is_chase(message: dict[str, Any]) -> bool:
    return bool(_SENDER_RE.search(get_header(message, "From")))


def parse(message: dict[str, Any]) -> Transaction | None:
    """Parse a Chase transaction alert. Returns None if not a Chase email."""
    if not is_chase(message):
        return None

    body = get_body(message)
    subject = get_header(message, "Subject")
    text = f"{subject}\n{body}"

    amount = parse_amount(text)
    if amount is None:
        return None

    merchant_raw = _extract_merchant(subject, body)
    if not merchant_raw:
        return None

    timestamp = parse_date(text) or parse_email_date(message)
    return Transaction(
        id=message["id"],
        amount=amount,
        merchant_raw=merchant_raw,
        card_issuer=CardIssuer.CHASE,
        timestamp=timestamp,
        source_email_id=message["id"],
    )


def _extract_merchant(subject: str, body: str) -> str | None:
    # Body is most specific — try it first
    for pattern in (_BODY_RE, _WITH_RE):
        m = pattern.search(body)
        if m:
            return m.group(1).strip().rstrip(".")
    # Subject is reliable for Chase; strip trailing punctuation / amounts
    m = _SUBJECT_RE.search(subject)
    if m:
        raw = m.group(1).strip()
        # Remove trailing " ending XXXX" or similar fragments
        raw = re.sub(r"\s+ending\s+\d+.*$", "", raw, flags=re.IGNORECASE)
        return raw.rstrip(".")
    return None
