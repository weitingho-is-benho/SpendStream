"""Extract structured transaction data from raw Gmail message dicts."""

from typing import Any

from spendstream.models import Transaction
from spendstream.parsers import parse_amex, parse_bofa, parse_capital_one, parse_chase

_PARSERS = [parse_amex, parse_chase, parse_bofa, parse_capital_one]


def parse_email(raw_message: dict[str, Any]) -> Transaction | None:
    """Try each bank parser in turn; return the first match or None."""
    for parser in _PARSERS:
        result = parser(raw_message)
        if result is not None:
            return result
    return None
