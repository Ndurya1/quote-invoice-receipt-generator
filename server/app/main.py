from fastapi import FastAPI

from app.api.v1 import router
from app.common.errors import register_exception_handlers
from app.common.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_environment()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="generate quotes, invoices and receipts all in one place",
        # Framework debug responses expose tracebacks and bypass our 500 handler.
        debug=False,
    )
    application.state.settings = settings
    register_exception_handlers(application)
    application.include_router(router)

    @application.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
