"""Typed representation of a persisted client row."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Client(BaseModel):
    """An existing client row, not a client creation request schema."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    name: str
    email: str | None
    phone: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime
