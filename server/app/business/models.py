from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BusinessProfile(BaseModel):
    """An existing business profile row, not a registration request schema."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    business_name: str
    email: str
    phone: str | None
    business_address: str
    logo_url: str | None
    default_currency: str
    created_at: datetime
    updated_at: datetime