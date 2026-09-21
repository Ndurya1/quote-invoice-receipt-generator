"""Authenticated Invoice endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.errors import DomainError
from app.common.responses import collection_response, resource_response
from app.invoices.queries import get_invoice_for_user, paginate_invoices_for_user
from app.invoices.schemas import InvoiceCreate, InvoiceDetail, InvoiceListResponse, InvoiceResponse
from app.invoices.service import create_invoice

router = APIRouter(prefix='/invoices', tags=['invoices'])


@router.get('', response_model=InvoiceListResponse)
def list_invoices(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    invoices, total = paginate_invoices_for_user(
        connection, user_id=user.id, page=page, page_size=page_size,
    )
    details = [InvoiceDetail(**row.invoice.model_dump(), items=row.items) for row in invoices]
    response = collection_response(details, page=page, page_size=page_size, total=total)
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('/{invoice_id}', response_model=InvoiceResponse)
def read_invoice(
    invoice_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    loaded = get_invoice_for_user(connection, user_id=user.id, invoice_id=invoice_id)
    if loaded is None:
        raise DomainError('INVOICE_NOT_FOUND', 'Invoice not found.', status_code=404)
    response = resource_response(InvoiceDetail(**loaded.invoice.model_dump(), items=loaded.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('', status_code=201, response_model=InvoiceResponse)
def create(
    payload: InvoiceCreate,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    created = create_invoice(connection, user_id=user.id, payload=payload)
    detail = InvoiceDetail(**created.invoice.model_dump(), items=created.items)
    response = resource_response(detail, status_code=201)
    response.headers['Cache-Control'] = 'no-store'
    return response
