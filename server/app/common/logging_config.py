"""Safe, environment-aware logging configuration for the API."""

import logging
import os
import re
from logging.config import dictConfig


_SENSITIVE_VALUE = re.compile(
    r"(?i)(password|token|secret|authorization|database_url)(\s*[:=]\s*)([^\s,;]+)"
)


class SensitiveDataFilter(logging.Filter):
    """Redact common credential-shaped values from application log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        record.msg = _SENSITIVE_VALUE.sub(r"\1\2[REDACTED]", message)
        record.args = ()
        return True


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"sensitive": {"()": SensitiveDataFilter}},
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["sensitive"],
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {"app": {"handlers": ["default"], "level": level, "propagate": False}},
        }
    )
