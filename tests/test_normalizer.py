import pytest

from spendstream.models import Transaction
from spendstream.normalizer import normalize


def test_normalize_not_implemented(sample_transaction: Transaction) -> None:
    with pytest.raises(NotImplementedError):
        normalize(sample_transaction)
