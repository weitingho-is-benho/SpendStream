from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class CardIssuer(str, Enum):
    AMEX = "amex"
    CHASE = "chase"
    BOFA = "bofa"
    CAPITAL_ONE = "capital_one"
    UNKNOWN = "unknown"


class Transaction(BaseModel):
    id: str
    amount: Decimal
    currency: str = "USD"
    merchant_raw: str
    merchant: str | None = None
    category: str | None = None
    card_issuer: CardIssuer = CardIssuer.UNKNOWN
    timestamp: datetime
    source_email_id: str


class Category(BaseModel):
    name: str
    keywords: list[str] = []
