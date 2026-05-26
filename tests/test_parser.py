import pytest

from spendstream.parser import parse_email


def test_parse_email_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        parse_email({})
