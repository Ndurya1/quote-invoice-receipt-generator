from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response
from app.receipts.schemas import ReceiptCreate, ReceiptDetail, ReceiptResponse
from app.receipts.service import create_receipt

router = APIRouter(prefix='/receipts', tags=['receipts'])


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