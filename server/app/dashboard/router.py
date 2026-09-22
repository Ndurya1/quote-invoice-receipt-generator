"""Authenticated dashboard endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response
from app.dashboard.schemas import DashboardSummaryResponse
from app.dashboard.service import get_dashboard_summary

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/summary', response_model=DashboardSummaryResponse)
def summary(
    user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    response = resource_response(get_dashboard_summary(connection, user_id=user.id))
    response.headers['Cache-Control'] = 'no-store'
    return response
