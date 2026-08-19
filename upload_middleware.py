"""Upload admission, concurrency, and request-size limits."""

from __future__ import annotations

import asyncio

from fastapi.responses import JSONResponse
from starlette.formparsers import MultiPartParser
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from config import INVALID_IMAGE_MESSAGE


class _RequestBodyTooLarge(Exception):
    pass


def configure_multipart_parser(max_bytes: int) -> None:
    """Keep accepted uploads in memory under the ASGI request limit."""

    MultiPartParser.spool_max_size = max_bytes


class InMemoryRequestLimitMiddleware:
    """Admit one valid-size multipart upload before form parsing begins."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self._processing_gate = asyncio.Semaphore(1)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("path") != "/remove-background"
            or scope.get("method") != "POST"
        ):
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_type = headers.get(b"content-type", b"").lower()
        if not content_type.startswith(b"multipart/form-data"):
            # Reject other form encodings before Starlette parses them.
            await self._reject(scope, receive, send)
            return

        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                await self._reject(scope, receive, send)
                return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _RequestBodyTooLarge
            return message

        try:
            # Acquiring the gate before multipart parsing bounds queued request
            # bodies as well as decoded images and model tensors.
            async with self._processing_gate:
                await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            await self._reject(scope, receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=400,
            content={"detail": INVALID_IMAGE_MESSAGE},
        )
        await response(scope, receive, send)
