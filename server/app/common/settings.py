"""Environment-driven application settings; database settings live in database.py."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "quote-invoice-receipt generator API"
    environment: str = "development"
    debug: bool = False
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://localhost:3000",
    )

    @classmethod
    def from_environment(cls) -> "Settings":
        debug = os.getenv("APP_DEBUG", "false").strip().lower()
        if debug not in {"true", "false"}:
            raise ValueError("APP_DEBUG must be true or false")
        environment = os.getenv("APP_ENV", "development").strip()
        if environment not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test, or production")
        name = os.getenv("APP_NAME", cls.app_name).strip()
        if not name:
            raise ValueError("APP_NAME must not be empty")
        configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        origins = tuple(origin.strip().rstrip("/") for origin in configured_origins.split(",") if origin.strip())
        if not origins and environment != "production":
            origins = cls.cors_origins
        if any(origin == "*" for origin in origins):
            raise ValueError("CORS_ALLOWED_ORIGINS must not contain a wildcard")
        return cls(
            app_name=name,
            environment=environment,
            debug=debug == "true",
            cors_origins=origins,
        )
