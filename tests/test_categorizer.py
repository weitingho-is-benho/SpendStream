import pytest

from spendstream.categorizer import _apply_rules, categorize
from spendstream.models import Transaction


@pytest.mark.parametrize(
    "merchant,expected",
    [
        ("Whole Foods Market", "Groceries"),
        ("Starbucks #4521", "Dining"),
        ("Uber Trip", "Transport"),
        ("Verizon Wireless", "Utilities"),
        ("Random Store XYZ", None),
    ],
)
def test_apply_rules(merchant: str, expected: str | None) -> None:
    assert _apply_rules(merchant) == expected


def test_categorize_not_implemented(sample_transaction: Transaction) -> None:
    with pytest.raises(NotImplementedError):
        categorize(sample_transaction)
