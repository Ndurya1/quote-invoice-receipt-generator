"""Version-one namespace; domain routers will be added in their own tasks."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.common.responses import resource_response

router = APIRouter(prefix="/api/v1")


@router.get("", tags=["system"])
async def api_root() -> JSONResponse:
    return resource_response({"version": "v1"})
