"""Version-one namespace; domain routers will be added in their own tasks."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("", tags=["system"])
async def api_root() -> dict[str, str]:
    return {"version": "v1"}
