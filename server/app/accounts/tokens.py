"""JWT issuance and strict token verification."""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt

from app.accounts.schemas import AccessToken, TokenPair
from app.common.errors import DomainError

ALGORITHM = "HS256"
ISSUER = "plug-and-send-billing"
AUDIENCE = "billing-api"


@dataclass(frozen=True)
class TokenSettings:
    secret_key: str = field(repr=False)
    access_minutes: int = 15
    refresh_days: int = 7

    def __post_init__(self) -> None:
        if not self.secret_key.strip() or len(self.secret_key.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must be a random secret of at least 32 bytes")
        if self.access_minutes <= 0 or self.refresh_days <= 0:
            raise ValueError("JWT lifetimes must be positive")
        try:
            access = timedelta(minutes=self.access_minutes)
            refresh = timedelta(days=self.refresh_days)
            datetime.now(timezone.utc) + refresh
        except OverflowError:
            raise ValueError("JWT lifetimes exceed the supported range") from None
        if refresh <= access:
            raise ValueError("Refresh tokens must outlive access tokens")

    @classmethod
    def from_environment(cls) -> "TokenSettings":
        try:
            access = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))
            refresh = int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7"))
        except ValueError:
            raise ValueError("JWT lifetimes must be integer values") from None
        return cls(os.getenv("JWT_SECRET_KEY", ""), access, refresh)


def get_token_settings() -> TokenSettings:
    return TokenSettings.from_environment()


def _encode_token(
    user_id: UUID, settings: TokenSettings, *, token_type: str,
    issued_at: datetime, lifetime: timedelta,
) -> str:
    return jwt.encode(
        {
            "sub": str(user_id), "type": token_type,
            "iat": issued_at, "exp": issued_at + lifetime,
            "jti": str(uuid4()), "iss": ISSUER, "aud": AUDIENCE,
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def issue_token_pair(user_id: UUID, settings: TokenSettings) -> TokenPair:
    now = datetime.now(timezone.utc)
    return TokenPair(
        access_token=_encode_token(user_id, settings, token_type="access", issued_at=now,
                                   lifetime=timedelta(minutes=settings.access_minutes)),
        refresh_token=_encode_token(user_id, settings, token_type="refresh", issued_at=now,
                                    lifetime=timedelta(days=settings.refresh_days)),
    )


def issue_access_token(user_id: UUID, settings: TokenSettings) -> AccessToken:
    return AccessToken(access_token=_encode_token(
        user_id, settings, token_type="access", issued_at=datetime.now(timezone.utc),
        lifetime=timedelta(minutes=settings.access_minutes),
    ))


def invalid_refresh_token() -> DomainError:
    return DomainError(
        "INVALID_REFRESH_TOKEN", "The refresh token is invalid or expired.",
        status_code=401, headers={"WWW-Authenticate": "Bearer"},
    )


def verify_refresh_token(token: str, settings: TokenSettings) -> UUID:
    return _verify_token(token, settings, token_type="refresh", error=invalid_refresh_token())


def authentication_required() -> DomainError:
    return DomainError(
        "AUTHENTICATION_REQUIRED", "Authentication is required.",
        status_code=401, headers={"WWW-Authenticate": "Bearer"},
    )


def verify_access_token(token: str, settings: TokenSettings) -> UUID:
    return _verify_token(token, settings, token_type="access", error=authentication_required())


def _verify_token(
    token: str, settings: TokenSettings, *, token_type: str, error: DomainError,
) -> UUID:
    """Return the verified subject; never trust a token's algorithm or raw claims."""
    try:
        claims = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM], issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["sub", "type", "iat", "exp", "jti", "iss", "aud"],
                     "strict_aud": True},
        )
        if claims["type"] != token_type:
            raise ValueError("Wrong token type")
        if type(claims["iat"]) is not int or type(claims["exp"]) is not int:
            raise ValueError("Token timestamps must be integers")
        if claims["exp"] <= claims["iat"]:
            raise ValueError("Invalid token lifetime")
        if not isinstance(claims["jti"], str) or not isinstance(claims["sub"], str):
            raise ValueError("Token identifiers must be strings")
        UUID(claims["jti"])
        return UUID(claims["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError):
        raise error from None
