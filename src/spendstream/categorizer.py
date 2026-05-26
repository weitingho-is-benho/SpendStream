"""Categorize transactions: deterministic rules first, Claude API fallback."""

from spendstream.models import Category, Transaction

RULES: list[Category] = [
    Category(name="Groceries", keywords=["whole foods", "safeway", "trader joe"]),
    Category(name="Dining", keywords=["mcdonald", "starbucks", "doordash", "uber eats"]),
    Category(name="Transport", keywords=["uber", "lyft", "mta", "caltrain"]),
    Category(name="Utilities", keywords=["pg&e", "comcast", "verizon", "at&t"]),
]


def categorize(transaction: Transaction) -> Transaction:
    """Return the transaction with category set. Uses rules; falls back to Claude API."""
    raise NotImplementedError


def _apply_rules(merchant: str) -> str | None:
    """Return the first matching category name, or None."""
    lower = merchant.lower()
    for rule in RULES:
        if any(kw in lower for kw in rule.keywords):
            return rule.name
    return None


def _categorize_with_ai(merchant: str) -> str:
    """Call Claude API to categorize a merchant string. Returns a category name."""
    raise NotImplementedError
