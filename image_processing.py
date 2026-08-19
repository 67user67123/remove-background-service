"""Input validation and in-memory image processing."""

from __future__ import annotations

import logging
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from config import (
    INFERENCE_ERROR_MESSAGE,
    INVALID_IMAGE_MESSAGE,
    MAX_IMAGE_PIXELS,
    SUPPORTED_IMAGE_FORMATS,
)
from model import BackgroundRemover


logger = logging.getLogger(__name__)


def decode_image(payload: bytes) -> Image.Image:
    """Validate and decode a supported image entirely from memory."""

    if not payload:
        raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)

    try:
        # Restrict decoder selection before opening attacker-controlled bytes.
        with Image.open(BytesIO(payload), formats=("JPEG", "PNG")) as uploaded:
            if uploaded.format not in SUPPORTED_IMAGE_FORMATS:
                raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)

            width, height = uploaded.size
            if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE)

            uploaded.load()
            return ImageOps.exif_transpose(uploaded).convert("RGB")
    except HTTPException:
        raise
    except (
        EOFError,
        Image.DecompressionBombError,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
        ValueError,
    ):
        raise HTTPException(status_code=400, detail=INVALID_IMAGE_MESSAGE) from None


def decode_remove_and_encode(
    payload: bytes,
    remover: BackgroundRemover,
) -> BytesIO:
    """Decode an image, remove its background, and encode an RGBA PNG."""

    # Decode errors remain client errors; only model/output errors become 500.
    image = decode_image(payload)
    original_size = image.size

    try:
        result = remover.remove_background(image)
        if not isinstance(result, Image.Image) or result.size != original_size:
            raise RuntimeError("Model returned an invalid image")

        output = BytesIO()
        result.convert("RGBA").save(output, format="PNG")
        output.seek(0)
        return output
    except Exception:
        logger.exception("Background-removal inference failed")
        raise HTTPException(
            status_code=500,
            detail=INFERENCE_ERROR_MESSAGE,
        ) from None
