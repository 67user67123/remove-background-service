"""HTTP routes for the web interface and image-processing API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from config import (
    INDEX_FILE,
    INVALID_IMAGE_MESSAGE,
    MAX_UPLOAD_BYTES,
    SUPPORTED_MEDIA_TYPES,
)
from image_processing import decode_remove_and_encode
from model import BackgroundRemover


router = APIRouter()


def get_background_remover(request: Request) -> BackgroundRemover:
    """Return the model instance created during application startup."""

    remover = getattr(request.app.state, "background_remover", None)
    if remover is None:
        raise RuntimeError("Background remover is not initialized")
    return remover


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    if INDEX_FILE.is_file():
        return FileResponse(INDEX_FILE, media_type="text/html")
    return HTMLResponse("<h1>Background Removal MVP</h1>")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/remove-background",
    response_class=StreamingResponse,
    responses={
        200: {"content": {"image/png": {}}},
        400: {"description": "Unsupported, invalid, empty, or oversized image"},
        500: {"description": "Model inference failed"},
    },
)
async def remove_background(
    file: UploadFile = File(...),
    remover: BackgroundRemover = Depends(get_background_remover),
) -> StreamingResponse:
    media_type = (file.content_type or "").partition(";")[0].strip().lower()
    if media_type not in SUPPORTED_MEDIA_TYPES:
        await file.close()
        raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)

    try:
        if file.size is not None and file.size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)
        payload = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)

    output = await run_in_threadpool(decode_remove_and_encode, payload, remover)
    return StreamingResponse(
        output,
        media_type="image/png",
        headers={
            "Content-Disposition": 'attachment; filename="removed-background.png"'
        },
    )
