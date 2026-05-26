from datetime import datetime
from decimal import Decimal

import pytest

from spendstream.models import Transaction


@pytest.fixture
def sample_transaction() -> Transaction:
    return Transaction(
        id="msg_001",
        amount=Decimal("42.50"),
        merchant_raw="WHOLEFDS #123 AUSTIN TX",
        timestamp=datetime(2024, 1, 15, 14, 30),
        source_email_id="gmail_abc123",
    )
