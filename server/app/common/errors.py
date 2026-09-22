"""Public domain errors and centralized HTTP exception responses."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from starlette.exceptions import HTTPException

from app.common.responses import error_response


logger = logging.getLogger("app.errors")


class DomainError(Exception):
    """An expected failure containing only information safe for API clients."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if not 400 <= status_code < 500:
            raise ValueError("DomainError requires a 4xx status code")
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers


HTTP_ERRORS = {
    400: ("BAD_REQUEST", "The request could not be processed."),
    401: ("AUTHENTICATION_REQUIRED", "Authentication is required."),
    403: ("FORBIDDEN_RESOURCE", "Access to this resource is forbidden."),
    404: ("RESOURCE_NOT_FOUND", "The requested resource was not found."),
    405: ("METHOD_NOT_ALLOWED", "This HTTP method is not allowed."),
    409: ("STATE_CONFLICT", "The request conflicts with the current resource state."),
    422: ("VALIDATION_ERROR", "Request validation failed."),
    429: ("TOO_MANY_REQUESTS", "Too many requests."),
}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return error_response(
        exc.code, exc.message, status_code=exc.status_code,
        details=exc.details, headers=exc.headers,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Never return raw inputs, custom validator messages, or exception context.
    errors = [
        {
            "loc": list(error["loc"]),
            "type": error["type"],
            "message": "Field is required." if error["type"] == "missing" else "Invalid value.",
        }
        for error in exc.errors()
    ]
    return error_response(
        "VALIDATION_ERROR", "Request validation failed.",
        status_code=422, details={"errors": errors},
    )


async def http_error_handler(request: Request, exc: HTTPException) -> Response:
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=exc.headers)
    if exc.status_code >= 500:
        code, message = "INTERNAL_SERVER_ERROR", "An unexpected server error occurred."
    else:
        code, message = HTTP_ERRORS.get(exc.status_code, ("HTTP_ERROR", "The request failed."))
    # Intentional domain messages belong in DomainError, not arbitrary HTTP details.
    return error_response(code, message, status_code=exc.status_code, headers=exc.headers)


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled application error method=%s path=%s error_type=%s",
        request.method, request.url.path, type(exc).__name__,
    )
    return error_response(
        "INTERNAL_SERVER_ERROR", "An unexpected server error occurred.", status_code=500,
    )


def register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(DomainError, domain_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(Exception, unexpected_error_handler)
