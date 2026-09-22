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
from app.pdf.context import build_receipt_context
from app.pdf.receipt import render_receipt_pdf
from app.receipts.queries import get_receipt_for_user, paginate_receipts_for_user
from app.receipts.schemas import ReceiptCreate, ReceiptDetail, ReceiptListResponse, ReceiptPatch, ReceiptResponse
from app.receipts.service import create_receipt, delete_receipt, update_receipt

router = APIRouter(prefix='/receipts', tags=['receipts'])


@router.get('/{receipt_id}/pdf', response_class=Response, responses={200: {'content': {'application/pdf': {}}}})
def receipt_pdf(
    receipt_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> Response:
    context = build_receipt_context(connection, user_id=user.id, receipt_id=receipt_id)
    return Response(
        content=render_receipt_pdf(context), media_type='application/pdf',
        headers={
            'Cache-Control': 'no-store',
            'Content-Disposition': f'attachment; filename="{context.document_number}.pdf"',
        },
    )


@router.get('', response_model=ReceiptListResponse)
def list_receipts(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    client_id: UUID | None = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    sort: Annotated[str | None, Query(max_length=32)] = None,
) -> JSONResponse:
    receipts, total = paginate_receipts_for_user(
        connection, user_id=user.id, page=page, page_size=page_size,
        client_id=client_id, search=search, sort=sort,
    )
    details = [ReceiptDetail(**row.receipt.model_dump(), items=row.items) for row in receipts]
    response = collection_response(details, page=page, page_size=page_size, total=total)
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('/{receipt_id}', response_model=ReceiptResponse)
def read_receipt(
    receipt_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    loaded = get_receipt_for_user(connection, user_id=user.id, receipt_id=receipt_id)
    if loaded is None:
        raise DomainError('RECEIPT_NOT_FOUND', 'Receipt not found.', status_code=404)
    response = resource_response(ReceiptDetail(**loaded.receipt.model_dump(), items=loaded.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.patch('/{receipt_id}', response_model=ReceiptResponse)
def patch_receipt(
    receipt_id: UUID,
    payload: ReceiptPatch,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    updated = update_receipt(connection, user_id=user.id, receipt_id=receipt_id, payload=payload)
    response = resource_response(ReceiptDetail(**updated.receipt.model_dump(), items=updated.items))
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.delete('/{receipt_id}', status_code=204, response_class=Response)
def remove_receipt(
    receipt_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> Response:
    delete_receipt(connection, user_id=user.id, receipt_id=receipt_id)
    return Response(status_code=204, headers={'Cache-Control': 'no-store'})


@router.post('', status_code=201, response_model=ReceiptResponse)
def create(
    payload: ReceiptCreate,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    created = create_receipt(connection, user_id=user.id, payload=payload)
    detail = ReceiptDetail(**created.receipt.model_dump(), items=created.items)
    response = resource_response(detail, status_code=201)
    response.headers['Cache-Control'] = 'no-store'
    return response
