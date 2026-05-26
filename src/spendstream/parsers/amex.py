"""Parser for American Express transaction notification emails."""

import re
from datetime import datetime
from typing import Any

from spendstream.gmail import get_body, get_header
from spendstream.models import CardIssuer, Transaction
from spendstream.parsers._utils import parse_amount, parse_date, parse_email_date

_SENDER_RE = re.compile(r"americanexpress\.com", re.IGNORECASE)

# "A charge of $42.50 has been made ... at MERCHANT on DATE"
# "A charge of $42.50 was made at MERCHANT"
_CHARGE_RE = re.compile(
    r"(?:charge|transaction)\s+of\s+\$[\d,\.]+\s+(?:has been|was)\s+(?:made|approved)"
    r"(?:\s+to\s+your[^.]+)?\s+at\s+([^\.]{2,60}?)(?:\s+on\s|\s*\.|$)",
    re.IGNORECASE,
)
# "at MERCHANT." or "at MERCHANT on DATE"
_AT_RE = re.compile(
    r"\bat\s+([A-Z][^$\n\r]{2,60}?)(?:\s+on\s+|\s*\.\s*|\s*$)",
    re.IGNORECASE,
)
# "Merchant: MERCHANT NAME" in structured emails
_MERCHANT_LABEL_RE = re.compile(
    r"Merchant(?:\s+Name)?[:\s]+([^\n\r]{2,60})",
    re.IGNORECASE,
)


def is_amex(message: dict[str, Any]) -> bool:
    return bool(_SENDER_RE.search(get_header(message, "From")))


def parse(message: dict[str, Any]) -> Transaction | None:
    """Parse an Amex transaction notification. Returns None if not an Amex email."""
    if not is_amex(message):
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
        card_issuer=CardIssuer.AMEX,
        timestamp=timestamp,
        source_email_id=message["id"],
    )


def _extract_merchant(text: str) -> str | None:
    for pattern in (_MERCHANT_LABEL_RE, _CHARGE_RE, _AT_RE):
        m = pattern.search(text)
        if m:
            return m.group(1).strip().rstrip(".")
    return None
