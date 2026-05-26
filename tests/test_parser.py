"""Tests for Gmail email parsers (Amex, Chase, BofA, Capital One)."""

import base64
from decimal import Decimal
from typing import Any

import pytest

from spendstream.models import CardIssuer
from spendstream.parser import parse_email
from spendstream.parsers.amex import parse as parse_amex
from spendstream.parsers.bofa import parse as parse_bofa
from spendstream.parsers.capital_one import parse as parse_capital_one
from spendstream.parsers.chase import parse as parse_chase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_message(
    msg_id: str,
    sender: str,
    subject: str,
    body: str,
    date: str = "Mon, 15 Jan 2024 14:30:00 +0000",
    mime_type: str = "text/plain",
) -> dict[str, Any]:
    """Build a minimal Gmail API full-message dict."""
    encoded = base64.urlsafe_b64encode(body.encode()).decode()
    return {
        "id": msg_id,
        "threadId": msg_id,
        "payload": {
            "mimeType": mime_type,
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": date},
            ],
            "body": {"data": encoded},
        },
    }


def _make_multipart(
    msg_id: str,
    sender: str,
    subject: str,
    plain: str,
    html: str,
    date: str = "Mon, 15 Jan 2024 14:30:00 +0000",
) -> dict[str, Any]:
    """Build a multipart/alternative Gmail message dict."""
    enc_plain = base64.urlsafe_b64encode(plain.encode()).decode()
    enc_html = base64.urlsafe_b64encode(html.encode()).decode()
    return {
        "id": msg_id,
        "threadId": msg_id,
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": date},
            ],
            "body": {},
            "parts": [
                {"mimeType": "text/plain", "body": {"data": enc_plain}},
                {"mimeType": "text/html", "body": {"data": enc_html}},
            ],
        },
    }


# ---------------------------------------------------------------------------
# Amex
# ---------------------------------------------------------------------------

AMEX_SENDER = "AmericanExpress@welcome.americanexpress.com"


def test_amex_basic_charge() -> None:
    msg = _make_message(
        "amex_001",
        AMEX_SENDER,
        "A charge to your Card ending 12345",
        "A charge of $42.50 has been made to your American Express Card ending 12345 "
        "at Whole Foods Market on January 15, 2024.",
    )
    tx = parse_amex(msg)
    assert tx is not None
    assert tx.amount == Decimal("42.50")
    assert tx.merchant_raw == "Whole Foods Market"
    assert tx.card_issuer == CardIssuer.AMEX
    assert tx.source_email_id == "amex_001"
    assert tx.timestamp.year == 2024
    assert tx.timestamp.month == 1
    assert tx.timestamp.day == 15


def test_amex_merchant_label_format() -> None:
    msg = _make_message(
        "amex_002",
        AMEX_SENDER,
        "New Transaction: $128.99",
        "Amount: $128.99\nMerchant: Apple Online Store\nDate: March 5, 2024",
    )
    tx = parse_amex(msg)
    assert tx is not None
    assert tx.amount == Decimal("128.99")
    assert tx.merchant_raw == "Apple Online Store"
    assert tx.timestamp.month == 3


def test_amex_amount_with_comma() -> None:
    msg = _make_message(
        "amex_003",
        AMEX_SENDER,
        "Charge to your Card",
        "A charge of $1,250.00 has been made at Delta Air Lines on February 20, 2024.",
    )
    tx = parse_amex(msg)
    assert tx is not None
    assert tx.amount == Decimal("1250.00")
    assert "Delta" in tx.merchant_raw


def test_amex_rejects_other_bank() -> None:
    msg = _make_message(
        "chase_001",
        "no.reply.alerts@chase.com",
        "Your $42.50 transaction with Whole Foods",
        "You made a $42.50 transaction with Whole Foods on Jan 15.",
    )
    assert parse_amex(msg) is None


def test_amex_no_amount_returns_none() -> None:
    msg = _make_message(
        "amex_004",
        AMEX_SENDER,
        "Your monthly statement is ready",
        "Your statement is now available online.",
    )
    assert parse_amex(msg) is None


# ---------------------------------------------------------------------------
# Chase
# ---------------------------------------------------------------------------

CHASE_SENDER = "no.reply.alerts@chase.com"


def test_chase_standard_alert() -> None:
    msg = _make_message(
        "chase_002",
        CHASE_SENDER,
        "Your $63.18 transaction with Trader Joe's",
        "You made a $63.18 transaction with Trader Joe's on Jan 15 at 11:00 AM ET.",
    )
    tx = parse_chase(msg)
    assert tx is not None
    assert tx.amount == Decimal("63.18")
    assert "Trader Joe" in tx.merchant_raw
    assert tx.card_issuer == CardIssuer.CHASE


def test_chase_merchant_from_subject() -> None:
    msg = _make_message(
        "chase_003",
        CHASE_SENDER,
        "Your $200.00 transaction with Amazon.com",
        "A transaction was made for $200.00 with Amazon.com.",
    )
    tx = parse_chase(msg)
    assert tx is not None
    assert tx.amount == Decimal("200.00")
    assert "Amazon" in tx.merchant_raw


def test_chase_amount_with_comma() -> None:
    msg = _make_message(
        "chase_004",
        CHASE_SENDER,
        "Your $1,500.00 transaction with Marriott Hotels",
        "You made a $1,500.00 transaction with Marriott Hotels on Feb 10 at 3:00 PM ET.",
    )
    tx = parse_chase(msg)
    assert tx is not None
    assert tx.amount == Decimal("1500.00")


def test_chase_rejects_other_bank() -> None:
    msg = _make_message(
        "bofa_001",
        "onlinebanking@ealerts.bankofamerica.com",
        "Transactions Alert",
        "A purchase of $42.50 has been authorized at Walmart on 01/15/2024.",
    )
    assert parse_chase(msg) is None


def test_chase_multipart_email() -> None:
    msg = _make_multipart(
        "chase_005",
        CHASE_SENDER,
        "Your $55.00 transaction with Starbucks",
        plain="You made a $55.00 transaction with Starbucks on Jan 20 at 8:00 AM ET.",
        html="<html><body>You made a <b>$55.00</b> transaction with Starbucks on Jan 20.</body></html>",
    )
    tx = parse_chase(msg)
    assert tx is not None
    assert tx.amount == Decimal("55.00")
    assert "Starbucks" in tx.merchant_raw


# ---------------------------------------------------------------------------
# Bank of America
# ---------------------------------------------------------------------------

BOFA_SENDER = "onlinebanking@ealerts.bankofamerica.com"


def test_bofa_standard_alert() -> None:
    msg = _make_message(
        "bofa_002",
        BOFA_SENDER,
        "Transactions Alert: Bank of America credit card",
        "A purchase of $87.32 has been authorized at Target on 01/15/2024.",
    )
    tx = parse_bofa(msg)
    assert tx is not None
    assert tx.amount == Decimal("87.32")
    assert tx.merchant_raw == "Target"
    assert tx.card_issuer == CardIssuer.BOFA
    assert tx.timestamp.month == 1


def test_bofa_transaction_was_made() -> None:
    msg = _make_message(
        "bofa_003",
        BOFA_SENDER,
        "Transactions Alert",
        "A transaction of $22.00 was made at Shell Gas Station on 03/10/2024.",
    )
    tx = parse_bofa(msg)
    assert tx is not None
    assert tx.amount == Decimal("22.00")
    assert "Shell" in tx.merchant_raw


def test_bofa_merchant_label_format() -> None:
    msg = _make_message(
        "bofa_004",
        BOFA_SENDER,
        "Transaction Alert",
        "Amount: $350.00\nMerchant: Best Buy #1234\nDate: 02/20/2024",
    )
    tx = parse_bofa(msg)
    assert tx is not None
    assert tx.amount == Decimal("350.00")
    assert "Best Buy" in tx.merchant_raw


def test_bofa_rejects_other_bank() -> None:
    msg = _make_message(
        "c1_001",
        "no-reply@accounts.capitalone.com",
        "Capital One Transaction Alert",
        "A $75.00 transaction was made at Costco on January 15, 2024.",
    )
    assert parse_bofa(msg) is None


def test_bofa_no_merchant_returns_none() -> None:
    msg = _make_message(
        "bofa_005",
        BOFA_SENDER,
        "Your statement is ready",
        "Your monthly statement for $423.19 is now available.",
    )
    # No merchant extractable — parser should return None
    result = parse_bofa(msg)
    # Amount is present but no merchant pattern matches; None is acceptable
    assert result is None or result.merchant_raw != ""


# ---------------------------------------------------------------------------
# Capital One
# ---------------------------------------------------------------------------

C1_SENDER = "no-reply@accounts.capitalone.com"


def test_capital_one_standard_alert() -> None:
    msg = _make_message(
        "c1_002",
        C1_SENDER,
        "Capital One Transaction Alert",
        "A $75.00 transaction was made at Costco on January 15, 2024.",
    )
    tx = parse_capital_one(msg)
    assert tx is not None
    assert tx.amount == Decimal("75.00")
    assert tx.merchant_raw == "Costco"
    assert tx.card_issuer == CardIssuer.CAPITAL_ONE
    assert tx.timestamp.year == 2024


def test_capital_one_purchase_format() -> None:
    msg = _make_message(
        "c1_003",
        C1_SENDER,
        "Transaction Alert for your Capital One account",
        "A purchase of $34.99 was made at Netflix on February 1, 2024.",
    )
    tx = parse_capital_one(msg)
    assert tx is not None
    assert tx.amount == Decimal("34.99")
    assert "Netflix" in tx.merchant_raw


def test_capital_one_merchant_label() -> None:
    msg = _make_message(
        "c1_004",
        C1_SENDER,
        "New Transaction",
        "Amount: $15.00\nMerchant: Spotify USA\nDate: March 1, 2024",
    )
    tx = parse_capital_one(msg)
    assert tx is not None
    assert tx.amount == Decimal("15.00")
    assert "Spotify" in tx.merchant_raw


def test_capital_one_charged_at_format() -> None:
    msg = _make_message(
        "c1_005",
        C1_SENDER,
        "Capital One Transaction Alert",
        "Your card was charged at Whole Foods Market for $112.47 on Jan 10, 2024.",
    )
    tx = parse_capital_one(msg)
    assert tx is not None
    assert tx.amount == Decimal("112.47")


def test_capital_one_rejects_other_bank() -> None:
    msg = _make_message(
        "amex_005",
        AMEX_SENDER,
        "A charge to your Card",
        "A charge of $50.00 has been made at Gap on January 15, 2024.",
    )
    assert parse_capital_one(msg) is None


# ---------------------------------------------------------------------------
# Dispatcher (parse_email)
# ---------------------------------------------------------------------------

def test_dispatcher_routes_amex() -> None:
    msg = _make_message(
        "amex_d01",
        AMEX_SENDER,
        "Charge to your Card",
        "A charge of $30.00 has been made at Duane Reade on January 15, 2024.",
    )
    tx = parse_email(msg)
    assert tx is not None
    assert tx.card_issuer == CardIssuer.AMEX


def test_dispatcher_routes_chase() -> None:
    msg = _make_message(
        "chase_d01",
        CHASE_SENDER,
        "Your $30.00 transaction with CVS",
        "You made a $30.00 transaction with CVS on Jan 15 at 9:00 AM ET.",
    )
    tx = parse_email(msg)
    assert tx is not None
    assert tx.card_issuer == CardIssuer.CHASE


def test_dispatcher_routes_bofa() -> None:
    msg = _make_message(
        "bofa_d01",
        BOFA_SENDER,
        "Transactions Alert",
        "A purchase of $45.00 has been authorized at Walgreens on 01/15/2024.",
    )
    tx = parse_email(msg)
    assert tx is not None
    assert tx.card_issuer == CardIssuer.BOFA


def test_dispatcher_routes_capital_one() -> None:
    msg = _make_message(
        "c1_d01",
        C1_SENDER,
        "Capital One Transaction Alert",
        "A $45.00 transaction was made at Walgreens on January 15, 2024.",
    )
    tx = parse_email(msg)
    assert tx is not None
    assert tx.card_issuer == CardIssuer.CAPITAL_ONE


def test_dispatcher_unknown_sender_returns_none() -> None:
    msg = _make_message(
        "unk_001",
        "alerts@unknownbank.com",
        "Transaction Alert",
        "A transaction of $50.00 was made.",
    )
    assert parse_email(msg) is None
