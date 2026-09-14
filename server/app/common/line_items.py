"""Shared input validation for Quote, Invoice, and Receipt line items."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LineItemInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    description: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3, allow_inf_nan=False)
    unit_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2, allow_inf_nan=False)
    position: int = Field(default=0, strict=True, ge=-2147483648, le=2147483647)

    @field_validator('description', mode='before')
    @classmethod
    def trim_description(cls, value):
        return value.strip() if isinstance(value, str) else value
