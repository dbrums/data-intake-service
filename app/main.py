from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.logging import LoggingMiddleware

setup_logging()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )
    app.add_middleware(LoggingMiddleware)
    app.include_router(api_router)
    return app


app = create_app()
