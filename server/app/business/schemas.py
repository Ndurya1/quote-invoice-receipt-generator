"""Business-profile response envelope."""

from pydantic import BaseModel

from app.business.models import BusinessProfile


class BusinessProfileResponse(BaseModel):
    data: BusinessProfile
