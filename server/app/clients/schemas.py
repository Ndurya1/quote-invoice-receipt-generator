"""Client creation input and public response envelope."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.clients.models import Client


class ClientCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str = Field(min_length=1, max_length=160)
    email: EmailStr | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None

    @field_validator('name', mode='before')
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class ClientPatch(ClientCreate):
    """Omission preserves a field; an explicitly supplied name cannot be null."""

    name: str | None = Field(default=None, min_length=1, max_length=160)

    @field_validator('name')
    @classmethod
    def reject_null_name(cls, value):
        if value is None:
            raise ValueError('Name cannot be null')
        return value


class ClientResponse(BaseModel):
    data: Client


class ClientPageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class ClientListResponse(BaseModel):
    data: list[Client]
    meta: ClientPageMeta
