"""Rendering DTOs built from persisted domain records."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.business.models import BusinessProfile
from app.clients.models import Client
from app.common.enums import DiscountType


class RenderItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class DocumentRenderContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_type: Literal['quote', 'invoice', 'receipt']
    document_id: UUID
    document_number: str
    issue_date: date
    secondary_date: date | None
    currency: str
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal
    total: Decimal
    status: str | None
    notes: str | None
    terms: str | None
    client: Client
    business: BusinessProfile | None
    items: tuple[RenderItem, ...]
    created_at: datetime
