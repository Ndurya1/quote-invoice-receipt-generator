"""Shared JSON response envelopes defined by API_CONTRACT.md."""

from decimal import Decimal
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _json_response(
    content: dict[str, Any],
    status_code: int,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    # Financial values stay decimal strings; UUIDs and dates use JSON-safe forms.
    encoded = jsonable_encoder(content, custom_encoder={Decimal: str})
    return JSONResponse(content=encoded, status_code=status_code, headers=headers)


def resource_response(data: Any, *, status_code: int = 200) -> JSONResponse:
    """Wrap a resource; callers supply an already-safe public representation."""
    return _json_response({"data": data}, status_code)


def collection_response(
    data: list[Any], *, page: int, page_size: int, total: int
) -> JSONResponse:
    """Wrap an already-paginated result and its total matching-record count."""
    return _json_response(
        {"data": data, "meta": {"page": page, "page_size": page_size, "total": total}},
        200,
    )


def error_response(
    code: str,
    message: str,
    *,
    status_code: int,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Format a public error; exception-to-error mapping belongs to Task 1.4."""
    return _json_response(
        {"error": {"code": code, "message": message, "details": details if details is not None else {}}},
        status_code,
        headers,
    )
