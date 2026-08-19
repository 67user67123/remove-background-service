from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import create_app


class FakeBackgroundRemover:
    def __init__(self) -> None:
        self.calls = 0

    def remove_background(self, image: Image.Image) -> Image.Image:
        self.calls += 1
        result = image.convert("RGBA")
        result.putalpha(Image.new("L", image.size, color=127))
        return result


def image_bytes(size: tuple[int, int] = (13, 7)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color=(30, 120, 210)).save(buffer, "PNG")
    return buffer.getvalue()


@pytest.fixture
def client_and_remover():
    remover = FakeBackgroundRemover()
    loader_calls = 0

    def fake_loader() -> FakeBackgroundRemover:
        nonlocal loader_calls
        loader_calls += 1
        return remover

    application = create_app(model_loader=fake_loader)
    with TestClient(application) as client:
        assert loader_calls == 1
        yield client, remover
    assert loader_calls == 1


def test_health(client_and_remover) -> None:
    client, _ = client_and_remover

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_is_served(client_and_remover) -> None:
    client, _ = client_and_remover
    root = client.get("/")

    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")

    assets = {
        "/static/css/base.css": "text/css",
        "/static/css/workspace.css": "text/css",
        "/static/css/result.css": "text/css",
        "/static/css/responsive.css": "text/css",
        "/static/js/app.js": "application/javascript",
    }
    for path, content_type in assets.items():
        assert path in root.text
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(content_type)
        assert response.content


def test_remove_background_returns_png(client_and_remover) -> None:
    client, remover = client_and_remover
    original_size = (13, 7)

    response = client.post(
        "/remove-background",
        files={"file": ("subject.png", image_bytes(original_size), "image/png")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-disposition"].endswith(
        'filename="removed-background.png"'
    )
    with Image.open(BytesIO(response.content)) as result:
        assert result.format == "PNG"
        assert result.mode == "RGBA"
        assert result.size == original_size
        assert result.getchannel("A").getextrema() == (127, 127)
    assert remover.calls == 1
