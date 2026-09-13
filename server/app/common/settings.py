"""Environment-driven application settings; database settings follow in Task 1.2."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "quote-invoice-receipt generator API"
    environment: str = "development"
    debug: bool = False

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
        return cls(app_name=name, environment=environment, debug=debug == "true")
