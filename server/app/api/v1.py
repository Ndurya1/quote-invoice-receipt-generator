"""Version-one namespace; domain routers will be added in their own tasks."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.accounts.router import router as accounts_router
from app.business.router import router as business_router
from app.clients.router import router as clients_router
from app.dashboard.router import router as dashboard_router
from app.invoices.router import router as invoices_router
from app.quotes.router import router as quotes_router
from app.receipts.router import router as receipts_router
from app.common.responses import resource_response

router = APIRouter(prefix="/api/v1")
router.include_router(accounts_router)
router.include_router(business_router)
router.include_router(clients_router)
router.include_router(quotes_router)
router.include_router(invoices_router)
router.include_router(receipts_router)
router.include_router(dashboard_router)


@router.get("", tags=["system"])
async def api_root() -> JSONResponse:
    return resource_response({"version": "v1"})
