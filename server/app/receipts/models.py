"""Typed persisted Receipt rows; request validation and lifecycle actions are separate."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.enums import DiscountType


class Receipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    client_id: UUID
    source_invoice_id: UUID | None
    receipt_number: str
    issue_date: date
    currency: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal
    total: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ReceiptItem(BaseModel):
    """Persisted line item; calculation and request validation happen before storage."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    receipt_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    position: int
