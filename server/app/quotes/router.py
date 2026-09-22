"""Authenticated Quote endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.errors import DomainError
from app.common.responses import collection_response, resource_response
from app.conversions.quote_invoice import convert_quote_to_invoice
from app.quotes.models import QuoteStatus
from app.quotes.queries import get_quote_for_user, paginate_quotes_for_user
from app.quotes.schemas import QuoteConvert, QuoteCreate, QuoteDetail, QuoteListResponse, QuotePatch, QuoteResponse
from app.invoices.schemas import InvoiceDetail, InvoiceResponse
from app.quotes.service import create_quote, delete_quote, transition_quote, update_quote

router = APIRouter(prefix='/quotes', tags=['quotes'])


@router.delete('/{quote_id}', status_code=204, response_class=Response)
def remove_quote(
    quote_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> Response:
    delete_quote(connection, user_id=user.id, quote_id=quote_id)
    return Response(status_code=204, headers={'Cache-Control': 'no-store'})


@router.patch('/{quote_id}', response_model=QuoteResponse)
def patch_quote(
    quote_id: UUID,
    payload: QuotePatch,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    updated = update_quote(connection, user_id=user.id, quote_id=quote_id, payload=payload)
    response = resource_response(QuoteDetail(**updated.quote.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('/{quote_id}', response_model=QuoteResponse)
def read_quote(
    quote_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    loaded = get_quote_for_user(connection, user_id=user.id, quote_id=quote_id)
    if loaded is None:
        raise DomainError('QUOTE_NOT_FOUND', 'Quote not found.', status_code=404)
    response = resource_response(QuoteDetail(**loaded.quote.model_dump(), items=loaded.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('', response_model=QuoteListResponse)
def list_quotes(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[QuoteStatus | None, Query()] = None,
    client_id: UUID | None = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    sort: Annotated[str | None, Query(max_length=32)] = None,
) -> JSONResponse:
    quotes, total = paginate_quotes_for_user(
        connection, user_id=user.id, page=page, page_size=page_size,
        status=status, client_id=client_id, search=search, sort=sort,
    )
    details = [QuoteDetail(**row.quote.model_dump(), items=row.items) for row in quotes]
    response = collection_response(details, page=page, page_size=page_size, total=total)
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('', status_code=201, response_model=QuoteResponse)
def create(
    payload: QuoteCreate,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    created = create_quote(connection, user_id=user.id, payload=payload)
    detail = QuoteDetail(**created.quote.model_dump(), items=created.items)
    response = resource_response(detail, status_code=201)
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{quote_id}/send', response_model=QuoteResponse)
def send_quote(
    quote_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    """Mark a draft as sent; delivery is handled outside this API."""
    updated = transition_quote(connection, user_id=user.id, quote_id=quote_id, target=QuoteStatus.SENT)
    response = resource_response(QuoteDetail(**updated.quote.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{quote_id}/accept', response_model=QuoteResponse)
def accept_quote(
    quote_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    """Accept an owned draft or sent quote."""
    updated = transition_quote(connection, user_id=user.id, quote_id=quote_id, target=QuoteStatus.ACCEPTED)
    response = resource_response(QuoteDetail(**updated.quote.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{quote_id}/reject', response_model=QuoteResponse)
def reject_quote(
    quote_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    """Reject an owned sent quote."""
    updated = transition_quote(connection, user_id=user.id, quote_id=quote_id, target=QuoteStatus.REJECTED)
    response = resource_response(QuoteDetail(**updated.quote.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{quote_id}/convert', status_code=201, response_model=InvoiceResponse)
def convert_quote(
    quote_id: UUID,
    payload: QuoteConvert,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    converted = convert_quote_to_invoice(
        connection, user_id=user.id, quote_id=quote_id,
        issue_date=payload.issue_date, due_date=payload.due_date,
    )
    detail = InvoiceDetail(**converted.invoice.model_dump(), items=converted.items)
    response = resource_response(detail, status_code=201)
    response.headers['Cache-Control'] = 'no-store'
    return response
