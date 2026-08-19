"""Application startup and shutdown lifecycle."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from model import BackgroundRemover, load_background_remover


ModelLoader = Callable[[], BackgroundRemover]
Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_lifespan(model_loader: ModelLoader | None = None) -> Lifespan:
    """Create a lifecycle that loads exactly one background-removal model."""

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        loader = model_loader or load_background_remover
        application.state.background_remover = await run_in_threadpool(loader)
        try:
            yield
        finally:
            application.state.background_remover = None

    return lifespan
