"""Parser for Capital One transaction alert emails."""

import re
from typing import Any

from spendstream.gmail import get_body, get_header
from spendstream.models import CardIssuer, Transaction
from spendstream.parsers._utils import parse_amount, parse_date, parse_email_date

_SENDER_RE = re.compile(r"capitalone\.com", re.IGNORECASE)

# "A $42.50 transaction was made at Whole Foods Market on January 15, 2024"
# "A purchase of $42.50 was made at MERCHANT on DATE"
_AT_RE = re.compile(
    r"(?:transaction|purchase)\s+(?:of\s+\$[\d,\.]+\s+)?was\s+made\s+at\s+"
    r"([A-Z][^$\n\r]{2,60}?)(?:\s+on\s+|\s*\.|$)",
    re.IGNORECASE,
)
# "charged at MERCHANT on DATE" or "charged at MERCHANT for $AMOUNT on DATE"
_CHARGE_AT_RE = re.compile(
    r"charged?\s+at\s+([A-Z][^$\n\r]{2,60}?)(?:\s+for\s+\$[\d,.]+)?(?:\s+on\s+|\s*\.|$)",
    re.IGNORECASE,
)
# "Merchant: MERCHANT NAME" (structured format)
_MERCHANT_LABEL_RE = re.compile(
    r"Merchant[:\s]+([^\n\r]{2,60})",
    re.IGNORECASE,
)
# "at MERCHANT" generic fallback
_GENERIC_AT_RE = re.compile(
    r"\bat\s+([A-Z][^$\n\r\.]{2,60}?)(?:\s+on\s+|\s*\.|$)",
    re.IGNORECASE,
)


def is_capital_one(message: dict[str, Any]) -> bool:
    return bool(_SENDER_RE.search(get_header(message, "From")))


def parse(message: dict[str, Any]) -> Transaction | None:
    """Parse a Capital One transaction alert. Returns None if not a Capital One email."""
    if not is_capital_one(message):
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
        card_issuer=CardIssuer.CAPITAL_ONE,
        timestamp=timestamp,
        source_email_id=message["id"],
    )


def _extract_merchant(text: str) -> str | None:
    for pattern in (_MERCHANT_LABEL_RE, _AT_RE, _CHARGE_AT_RE, _GENERIC_AT_RE):
        m = pattern.search(text)
        if m:
            return m.group(1).strip().rstrip(".")
    return None
