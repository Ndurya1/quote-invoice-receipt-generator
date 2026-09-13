"""Account HTTP endpoints under /api/v1/auth."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg import Connection

from app.accounts.schemas import RegistrationResponse, UserCreate, UserResponse
from app.accounts.service import create_user
from app.common.dependencies import get_database_connection
from app.common.responses import resource_response

router = APIRouter(prefix="/auth", tags=["accounts"])


@router.post("/register", status_code=201, response_model=RegistrationResponse)
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
