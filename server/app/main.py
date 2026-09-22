from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import router
from app.common.errors import register_exception_handlers
from app.common.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_environment()
    settings.validate_for_production()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="generate quotes, invoices and receipts all in one place",
        # Framework debug responses expose tracebacks and bypass our 500 handler.
        debug=False,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
    if settings.allowed_hosts:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
    if settings.force_https:
        application.add_middleware(HTTPSRedirectMiddleware)
    application.state.settings = settings
    register_exception_handlers(application)
    application.include_router(router)

    @application.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
