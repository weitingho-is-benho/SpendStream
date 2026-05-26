"""Normalize raw merchant strings into clean, consistent names."""

from spendstream.models import Transaction


def normalize(transaction: Transaction) -> Transaction:
    """Return a copy of the transaction with merchant field populated from merchant_raw."""
    raise NotImplementedError
