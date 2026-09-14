"""Authenticated Client endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.clients.queries import get_client_for_user, paginate_clients_for_user
from app.clients.schemas import ClientCreate, ClientListResponse, ClientPatch, ClientResponse
from app.clients.service import create_client, update_client
from app.common.dependencies import get_database_connection
from app.common.errors import DomainError
from app.common.responses import collection_response, resource_response

router = APIRouter(prefix='/clients', tags=['clients'])


@router.patch('/{client_id}', response_model=ClientResponse)
def patch_client(
    client_id: UUID,
    payload: ClientPatch,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    client = update_client(connection, user_id=user.id, client_id=client_id, payload=payload)
    response = resource_response(client)
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('/{client_id}', response_model=ClientResponse)
def read_client(
    client_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    client = get_client_for_user(connection, user_id=user.id, client_id=client_id)
    if client is None:
        raise DomainError('CLIENT_NOT_FOUND', 'Client not found.', status_code=404)
    response = resource_response(client)
    response.headers['Cache-Control'] = 'no-store'
    return response


@router.get('', response_model=ClientListResponse)
def list_clients(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
    page: Annotated[int, Query(ge=1, le=2147483647)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JSONResponse:
    clients, total = paginate_clients_for_user(
        connection, user_id=user.id, page=page, page_size=page_size,
    )
    response = collection_response(clients, page=page, page_size=page_size, total=total)
    response.headers['Cache-Control'] = 'no-store'
    return response


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
