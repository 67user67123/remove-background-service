"""Shared configuration for the web application."""

from pathlib import Path
from typing import Final


BASE_DIR: Final = Path(__file__).resolve().parent
STATIC_DIR: Final = BASE_DIR / "static"
INDEX_FILE: Final = STATIC_DIR / "index.html"

MAX_UPLOAD_BYTES: Final = 20 * 1024 * 1024
MAX_MULTIPART_OVERHEAD_BYTES: Final = 64 * 1024
MAX_REQUEST_BYTES: Final = MAX_UPLOAD_BYTES + MAX_MULTIPART_OVERHEAD_BYTES
MAX_IMAGE_PIXELS: Final = 40_000_000

SUPPORTED_MEDIA_TYPES: Final = frozenset({"image/jpeg", "image/jpg", "image/png"})
SUPPORTED_IMAGE_FORMATS: Final = frozenset({"JPEG", "PNG"})

INVALID_IMAGE_MESSAGE: Final = "Upload a valid JPG or PNG image no larger than 20 MiB."
INFERENCE_ERROR_MESSAGE: Final = "Background removal failed."
