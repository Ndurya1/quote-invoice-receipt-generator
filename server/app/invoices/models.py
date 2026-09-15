"""Typed persisted Invoice rows; request validation and lifecycle actions are separate."""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.enums import DiscountType


class InvoiceStatus(StrEnum):
    DRAFT = 'DRAFT'
    SENT = 'SENT'
    PAID = 'PAID'
    OVERDUE = 'OVERDUE'
    CANCELLED = 'CANCELLED'


class Invoice(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    client_id: UUID
    source_quote_id: UUID | None
    invoice_number: str
    issue_date: date
    due_date: date | None
    currency: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal
    total: Decimal
    status: InvoiceStatus
    notes: str | None
    terms: str | None
    created_at: datetime
    updated_at: datetime


class InvoiceItem(BaseModel):
    """Persisted line item; calculation and request validation happen before storage."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    invoice_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    position: int
