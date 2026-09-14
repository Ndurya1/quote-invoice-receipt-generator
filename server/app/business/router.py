"""Authenticated business-profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.business.queries import get_profile_for_user
from app.business.schemas import BusinessProfileResponse
from app.common.dependencies import get_database_connection
from app.common.errors import DomainError
from app.common.responses import resource_response

router = APIRouter(prefix='/business-profile', tags=['business'])


@router.get('', response_model=BusinessProfileResponse)
def read_profile(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    profile = get_profile_for_user(connection, user.id)
    if profile is None:
        raise DomainError(
            'BUSINESS_PROFILE_NOT_FOUND', 'Business profile not found.', status_code=404,
        )
    response = resource_response(profile)
    response.headers['Cache-Control'] = 'no-store'
    return response
