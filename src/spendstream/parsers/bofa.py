"""Parser for Bank of America transaction alert emails."""

import re
from typing import Any

from spendstream.gmail import get_body, get_header
from spendstream.models import CardIssuer, Transaction
from spendstream.parsers._utils import parse_amount, parse_date, parse_email_date

_SENDER_RE = re.compile(r"bankofamerica\.com", re.IGNORECASE)

# "A purchase of $42.50 has been authorized at MERCHANT on DATE"
# "A transaction of $42.50 was made at MERCHANT"
_AT_RE = re.compile(
    r"(?:purchase|transaction)\s+(?:of\s+\$[\d,\.]+\s+)?(?:has been|was)\s+"
    r"(?:authorized|made|processed)\s+at\s+([A-Z0-9][^$\n\r]{2,60}?)"
    r"(?:\s+on\s+|\s*\.|$)",
    re.IGNORECASE,
)
# "Merchant: MERCHANT NAME" (structured alert format)
_MERCHANT_LABEL_RE = re.compile(
    r"Merchant[:\s]+([^\n\r]{2,60})",
    re.IGNORECASE,
)
# Fallback: "authorized at MERCHANT"
_AUTHORIZED_AT_RE = re.compile(
    r"authorized\s+at\s+([A-Z0-9][^$\n\r\.]{2,60}?)(?:\s+on\s+|\s*\.|$)",
    re.IGNORECASE,
)


def is_bofa(message: dict[str, Any]) -> bool:
    return bool(_SENDER_RE.search(get_header(message, "From")))


def parse(message: dict[str, Any]) -> Transaction | None:
    """Parse a BofA transaction alert. Returns None if not a BofA email."""
    if not is_bofa(message):
        return None

    body = get_body(message)
    subject = get_header(message, "Subject")
    text = f"{subject}\n{body}"

    amount = parse_amount(text)
    if amount is None:
        return None

    merchant_raw = _extract_merchant(text)
    if not merchant_raw:
        return None

    timestamp = parse_date(text) or parse_email_date(message)
    return Transaction(
        id=message["id"],
        amount=amount,
        merchant_raw=merchant_raw,
        card_issuer=CardIssuer.BOFA,
        timestamp=timestamp,
        source_email_id=message["id"],
    )


def _extract_merchant(text: str) -> str | None:
    for pattern in (_MERCHANT_LABEL_RE, _AT_RE, _AUTHORIZED_AT_RE):
        m = pattern.search(text)
        if m:
            return m.group(1).strip().rstrip(".")
    return None
