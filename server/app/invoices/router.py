"""Authenticated Invoice endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response
from app.invoices.schemas import InvoiceCreate, InvoiceDetail, InvoiceResponse
from app.invoices.service import create_invoice

router = APIRouter(prefix='/invoices', tags=['invoices'])


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
