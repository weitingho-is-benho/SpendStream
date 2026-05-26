"""Extract structured transaction data from raw email bodies."""

from typing import Any

from spendstream.models import Transaction


def parse_email(raw_message: dict[str, Any]) -> Transaction | None:
    """Parse a raw Gmail message dict into a Transaction, or None if not a transaction email."""
    raise NotImplementedError
