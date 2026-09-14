"""Business-profile response envelope."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from app.business.models import BusinessProfile
from app.common.currency import CurrencyCode


class BusinessProfilePut(BaseModel):
    """Full replacement of editable fields; ownership comes from authentication."""

    model_config = ConfigDict(extra='forbid')

    business_name: str = Field(min_length=1, max_length=160)
    logo_url: HttpUrl | None = None
    email: EmailStr | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None
    tax_number: str | None = Field(default=None, max_length=100)
    default_currency: CurrencyCode = 'KES'

    @field_validator('business_name', mode='before')
    @classmethod
    def trim_business_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class BusinessProfileResponse(BaseModel):
    data: BusinessProfile
