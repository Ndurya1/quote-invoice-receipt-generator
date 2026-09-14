"""Shared currency-code format validation; no registry lookup or FX conversion."""

import re
from typing import Annotated

from pydantic import BeforeValidator


def validate_currency_code(value: object) -> str:
    """Return an unchanged code consisting of exactly three uppercase ASCII letters."""
    if not isinstance(value, str) or re.fullmatch(r"[A-Z]{3}", value) is None:
        raise ValueError("Currency must contain exactly three uppercase letters.")
    return value


CurrencyCode = Annotated[str, BeforeValidator(validate_currency_code)]
