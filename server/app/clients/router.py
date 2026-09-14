"""Authenticated Client endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.clients.schemas import ClientCreate, ClientResponse
from app.clients.service import create_client
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response

router = APIRouter(prefix='/clients', tags=['clients'])


@router.post('', status_code=201, response_model=ClientResponse)
def create(
    payload: ClientCreate,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    client = create_client(connection, user_id=user.id, payload=payload)
    response = resource_response(client, status_code=201)
    response.headers['Cache-Control'] = 'no-store'
    return response
