"""Shared domain enums used by billing documents."""

from enum import StrEnum


class DiscountType(StrEnum):
    NONE = 'NONE'
    FIXED = 'FIXED'
    PERCENTAGE = 'PERCENTAGE'
