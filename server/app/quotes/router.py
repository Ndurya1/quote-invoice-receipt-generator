"""Authenticated Quote endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response
from app.quotes.schemas import QuoteCreate, QuoteDetail, QuoteResponse
from app.quotes.service import create_quote

router = APIRouter(prefix='/quotes', tags=['quotes'])


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
