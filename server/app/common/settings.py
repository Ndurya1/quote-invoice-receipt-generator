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
    allowed_hosts: tuple[str, ...] = ()
    force_https: bool = False
    rate_limit_window_seconds: int = 60
    auth_rate_limit_per_window: int = 10
    refresh_rate_limit_per_window: int = 60
    pdf_rate_limit_per_window: int = 30
    rate_limit_max_keys: int = 10_000

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
        configured_hosts = os.getenv("ALLOWED_HOSTS", "")
        hosts = tuple(host.strip() for host in configured_hosts.split(",") if host.strip())
        force_https = os.getenv("APP_FORCE_HTTPS", "true" if environment == "production" else "false").strip().lower()
        if force_https not in {"true", "false"}:
            raise ValueError("APP_FORCE_HTTPS must be true or false")
        rate_limit_values = {
            "rate_limit_window_seconds": _positive_int_env("RATE_LIMIT_WINDOW_SECONDS", 60),
            "auth_rate_limit_per_window": _positive_int_env("AUTH_RATE_LIMIT_PER_WINDOW", 10),
            "refresh_rate_limit_per_window": _positive_int_env("REFRESH_RATE_LIMIT_PER_WINDOW", 60),
            "pdf_rate_limit_per_window": _positive_int_env("PDF_RATE_LIMIT_PER_WINDOW", 30),
            "rate_limit_max_keys": _positive_int_env("RATE_LIMIT_MAX_KEYS", 10_000),
        }
        if environment == "production":
            if debug == "true":
                raise ValueError("APP_DEBUG must be false in production")
            if not origins:
                raise ValueError("CORS_ALLOWED_ORIGINS is required in production")
            if not hosts:
                raise ValueError("ALLOWED_HOSTS is required in production")
        return cls(
            app_name=name,
            environment=environment,
            debug=debug == "true",
            cors_origins=origins,
            allowed_hosts=hosts,
            force_https=force_https == "true",
            **rate_limit_values,
        )

    def validate_for_production(self) -> None:
        if self.environment != "production":
            return
        if self.debug:
            raise ValueError("APP_DEBUG must be false in production")
        if not self.cors_origins:
            raise ValueError("CORS_ALLOWED_ORIGINS is required in production")
        if not self.allowed_hosts:
            raise ValueError("ALLOWED_HOSTS is required in production")
        from app.accounts.tokens import TokenSettings

        TokenSettings.from_environment()


def _positive_int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return parsed
