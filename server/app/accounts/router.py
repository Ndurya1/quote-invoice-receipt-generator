"""Account HTTP endpoints under /api/v1/auth."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.accounts.schemas import (
    CurrentUserResponse, LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    RegistrationResponse, UserCreate, UserResponse,
)
from app.accounts.service import authenticate_user, create_user, refresh_access_token
from app.accounts.tokens import TokenSettings, get_token_settings, issue_token_pair
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response
from app.common.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["accounts"])


@router.get("/me", response_model=CurrentUserResponse)
def current_user(user: Annotated[User, Depends(get_current_user)]) -> JSONResponse:
    response = resource_response(UserResponse.model_validate(user))
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/register", status_code=201, response_model=RegistrationResponse, dependencies=[Depends(rate_limit("auth"))])
def register(
    payload: UserCreate,
    connection: Annotated[Connection, Depends(get_database_connection)],
) -> JSONResponse:
    # password is excluded from model_dump(), so pass validated fields explicitly.
    user = create_user(
        connection, name=payload.name, email=str(payload.email),
        password=payload.password, phone=payload.phone,
    )
    return resource_response(UserResponse.model_validate(user), status_code=201)


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(rate_limit("auth"))])
def login(
    payload: LoginRequest,
    connection: Annotated[Connection, Depends(get_database_connection)],
    settings: Annotated[TokenSettings, Depends(get_token_settings)],
) -> JSONResponse:
    user = authenticate_user(connection, email=str(payload.email), password=payload.password)
    response = resource_response(issue_token_pair(user.id, settings))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


@router.post("/refresh", response_model=RefreshResponse, dependencies=[Depends(rate_limit("refresh"))])
def refresh(
    payload: RefreshRequest,
    connection: Annotated[Connection, Depends(get_database_connection)],
    settings: Annotated[TokenSettings, Depends(get_token_settings)],
) -> JSONResponse:
    token = refresh_access_token(connection, refresh_token=payload.refresh_token, settings=settings)
    response = resource_response(token)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response
