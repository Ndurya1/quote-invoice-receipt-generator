from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.responses import collection_response, resource_response
from app.receipts.queries import paginate_receipts_for_user
from app.receipts.schemas import ReceiptCreate, ReceiptDetail, ReceiptListResponse, ReceiptResponse
from app.receipts.service import create_receipt

router = APIRouter(prefix='/receipts', tags=['receipts'])


@router.get('', response_model=ReceiptListResponse)
def list_receipts(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    receipts, total = paginate_receipts_for_user(
        connection, user_id=user.id, page=page, page_size=page_size,
    )
    details = [ReceiptDetail(**row.receipt.model_dump(), items=row.items) for row in receipts]
    response = collection_response(details, page=page, page_size=page_size, total=total)
    response.headers['Cache-Control'] = 'no-store'
    return response


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
