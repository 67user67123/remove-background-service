"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import MAX_REQUEST_BYTES, STATIC_DIR
from lifespan import ModelLoader, create_lifespan
from routes import router
from upload_middleware import (
    InMemoryRequestLimitMiddleware,
    configure_multipart_parser,
)


def create_app(model_loader: ModelLoader | None = None) -> FastAPI:
    """Build the application, optionally using a lightweight test model."""

    configure_multipart_parser(MAX_REQUEST_BYTES)
    application = FastAPI(
        title="Background Removal MVP",
        version="1.0.0",
        lifespan=create_lifespan(model_loader),
    )
    application.add_middleware(
        InMemoryRequestLimitMiddleware,
        max_bytes=MAX_REQUEST_BYTES,
    )
    if STATIC_DIR.is_dir():
        application.mount(
            "/static",
            StaticFiles(directory=STATIC_DIR),
            name="static",
        )
    application.include_router(router)
    return application
