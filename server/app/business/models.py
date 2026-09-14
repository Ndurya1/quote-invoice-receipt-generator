from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BusinessProfile(BaseModel):
    """An existing business profile row, not a registration request schema."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    business_name: str
    email: str | None
    phone: str | None
    address: str | None
    tax_number: str | None
    logo_url: str | None
    default_currency: str
    created_at: datetime
    updated_at: datetime
