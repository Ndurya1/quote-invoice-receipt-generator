"""Authenticated Invoice endpoints."""

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
from app.pdf.context import build_invoice_context
from app.pdf.invoice import render_invoice_pdf
from app.invoices.models import InvoiceStatus
from app.invoices.queries import get_invoice_for_user, paginate_invoices_for_user
from app.invoices.schemas import InvoiceCreate, InvoiceDetail, InvoiceListResponse, InvoicePatch, InvoiceResponse
from app.invoices.service import create_invoice, delete_invoice, transition_invoice, update_invoice
from app.conversions.invoice_receipt import convert_invoice_to_receipt
from app.receipts.schemas import ReceiptConvert, ReceiptDetail, ReceiptResponse

router = APIRouter(prefix='/invoices', tags=['invoices'])


@router.get('/{invoice_id}/pdf', response_class=Response, responses={200: {'content': {'application/pdf': {}}}})
def invoice_pdf(
    invoice_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> Response:
    context = build_invoice_context(connection, user_id=user.id, invoice_id=invoice_id)
    return Response(
        content=render_invoice_pdf(context), media_type='application/pdf',
        headers={
            'Cache-Control': 'no-store',
            'Content-Disposition': f'attachment; filename="{context.document_number}.pdf"',
        },
    )


@router.get('', response_model=InvoiceListResponse)
def list_invoices(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[InvoiceStatus | None, Query()] = None,
    client_id: UUID | None = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    sort: Annotated[str | None, Query(max_length=32)] = None,
) -> JSONResponse:
    invoices, total = paginate_invoices_for_user(
        connection, user_id=user.id, page=page, page_size=page_size,
        status=status, client_id=client_id, search=search, sort=sort,
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


@router.patch('/{invoice_id}', response_model=InvoiceResponse)
def patch_invoice(
    invoice_id: UUID,
    payload: InvoicePatch,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    updated = update_invoice(connection, user_id=user.id, invoice_id=invoice_id, payload=payload)
    response = resource_response(InvoiceDetail(**updated.invoice.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.delete('/{invoice_id}', status_code=204, response_class=Response)
def remove_invoice(
    invoice_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> Response:
    delete_invoice(connection, user_id=user.id, invoice_id=invoice_id)
    return Response(status_code=204, headers={'Cache-Control': 'no-store'})


@router.post('/{invoice_id}/send', response_model=InvoiceResponse)
def send_invoice(
    invoice_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    updated = transition_invoice(connection, user_id=user.id, invoice_id=invoice_id, target=InvoiceStatus.SENT)
    response = resource_response(InvoiceDetail(**updated.invoice.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{invoice_id}/mark-paid', response_model=InvoiceResponse)
def mark_invoice_paid(
    invoice_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    updated = transition_invoice(connection, user_id=user.id, invoice_id=invoice_id, target=InvoiceStatus.PAID)
    response = resource_response(InvoiceDetail(**updated.invoice.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{invoice_id}/cancel', response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    updated = transition_invoice(connection, user_id=user.id, invoice_id=invoice_id, target=InvoiceStatus.CANCELLED)
    response = resource_response(InvoiceDetail(**updated.invoice.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.post('/{invoice_id}/convert', status_code=201, response_model=ReceiptResponse)
def convert_invoice(
    invoice_id: UUID,
    payload: ReceiptConvert,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    converted = convert_invoice_to_receipt(
        connection, user_id=user.id, invoice_id=invoice_id, issue_date=payload.issue_date,
    )
    detail = ReceiptDetail(**converted.receipt.model_dump(), items=converted.items)
    response = resource_response(detail, status_code=201)
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
