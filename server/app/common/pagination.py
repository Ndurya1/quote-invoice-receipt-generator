"""Shared collection pagination rules."""

from dataclasses import dataclass


MAX_PAGE = 2_147_483_647
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Pagination:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def validate_pagination(page: int, page_size: int) -> Pagination:
    if not 1 <= page <= MAX_PAGE or not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError('Invalid pagination bounds')
    return Pagination(page=page, page_size=page_size)
