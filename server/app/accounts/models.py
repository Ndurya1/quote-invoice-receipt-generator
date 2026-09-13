from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """An existing users row, not a registration request schema."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    email: str
    phone: str | None
    password_hash: str = Field(exclude=True, repr=False)
    created_at: datetime
    updated_at: datetime
