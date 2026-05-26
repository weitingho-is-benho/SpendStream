"""Sync transactions to a Google Sheets spreadsheet."""

from typing import Any

from spendstream.models import Transaction


def get_service() -> Any:
    """Return an authenticated Google Sheets API service object."""
    raise NotImplementedError


def append_transactions(service: Any, spreadsheet_id: str, transactions: list[Transaction]) -> None:
    """Append transactions as new rows in the spreadsheet."""
    raise NotImplementedError
