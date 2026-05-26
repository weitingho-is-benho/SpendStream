from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Transaction(BaseModel):
    id: str
    amount: Decimal
    currency: str = "USD"
    merchant_raw: str
    merchant: str | None = None
    category: str | None = None
    timestamp: datetime
    source_email_id: str


class Category(BaseModel):
    name: str
    keywords: list[str] = []
