import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def normalize_email(value):
    return value.strip().lower() if isinstance(value, str) else value


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=255)
    password: str = Field(exclude=True, repr=False)
    phone: str | None = Field(default=None, max_length=30)

    @field_validator('name', mode='before')
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('email', mode='before')
    @classmethod
    def validate_email_structure(cls, v:str)->str:
        return normalize_email(v)
    
    @field_validator('phone', mode='before')
    @classmethod
    def trim_phone(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            if not re.fullmatch(r'\+?[0-9]+', v):
                raise ValueError('Phone must contain digits with an optional leading +')
        return v

    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    phone: str | None = None


class RegistrationResponse(BaseModel):
    """Public registration envelope, also used to document the endpoint."""

    data: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(exclude=True, repr=False)

    @field_validator('email', mode='before')
    @classmethod
    def normalize_login_email(cls, value):
        return normalize_email(value)


class TokenPair(BaseModel):
    access_token: str = Field(repr=False)
    refresh_token: str = Field(repr=False)
    token_type: Literal['bearer'] = 'bearer'


class LoginResponse(BaseModel):
    data: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, exclude=True, repr=False)


class AccessToken(BaseModel):
    access_token: str = Field(repr=False)
    token_type: Literal['bearer'] = 'bearer'


class RefreshResponse(BaseModel):
    data: AccessToken

