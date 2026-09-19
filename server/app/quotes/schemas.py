"""Quote creation input; computed values and ownership are server-managed."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.currency import CurrencyCode
from app.common.enums import DiscountType
from app.common.line_items import LineItemInput
from app.quotes.models import Quote, QuoteItem


class QuoteDetail(Quote):
    items: tuple[QuoteItem, ...]


class QuoteResponse(BaseModel):
    data: QuoteDetail


class QuotePageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class QuoteListResponse(BaseModel):
    data: list[QuoteDetail]
    meta: QuotePageMeta


class QuoteCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    client_id: UUID
    issue_date: date
    expiry_date: date | None = None
    currency: CurrencyCode
    tax_rate: Decimal = Field(default=Decimal('0'), ge=0, max_digits=6,
                              decimal_places=3, allow_inf_nan=False)
    discount_type: DiscountType = DiscountType.NONE
    discount_value: Decimal = Field(default=Decimal('0'), ge=0, max_digits=14,
                                    decimal_places=2, allow_inf_nan=False)
    notes: str | None = None
    terms: str | None = None
    items: list[LineItemInput] = Field(min_length=1)

    @model_validator(mode='after')
    def validate_dates_and_discount(self):
        if self.expiry_date is not None and self.expiry_date < self.issue_date:
            raise ValueError('Expiry date cannot precede issue date')
        if self.discount_type == DiscountType.NONE and self.discount_value != 0:
            raise ValueError('NONE requires a zero discount value')
        if self.discount_type == DiscountType.PERCENTAGE and self.discount_value > 100:
            raise ValueError('Percentage discount cannot exceed 100')
        return self
