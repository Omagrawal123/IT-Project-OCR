"""Unit tests for API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    """Async test client for FastAPI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_root(client):
    """GET / returns API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health(client):
    """GET /health returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data


@pytest.mark.asyncio
async def test_extract_requires_file(client):
    """POST /api/v1/extract without file returns 422."""
    response = await client.post(
        f"/api/v1/extract",
        data={"lang": "de", "provider": "mock"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.slow
async def test_extract_mock_success(client, image_bytes_png):
    """POST /api/v1/extract with mock provider and valid image returns 200 (runs full pipeline + OCR)."""
    response = await client.post(
        "/api/v1/extract",
        data={
            "lang": "de",
            "timezone": "UTC",
            "provider": "mock",
        },
        files={"file": ("poster.png", image_bytes_png, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "event_poster"
    assert data.get("route") in ("ocr_first", "vision", "ocr_fallback_vision")
    assert "fields" in data
    assert "confidence" in data
    assert "warnings" in data


@pytest.mark.asyncio
async def test_extract_invalid_content_type(client, image_bytes_png):
    """POST /api/v1/extract with wrong content type returns 400."""
    response = await client.post(
        "/api/v1/extract",
        data={"lang": "de", "provider": "mock"},
        files={"file": ("x.txt", image_bytes_png, "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_extract_invalid_force_route(client, image_bytes_png):
    """POST /api/v1/extract with invalid force_route returns 400."""
    response = await client.post(
        "/api/v1/extract",
        data={"lang": "de", "provider": "mock", "force_route": "invalid"},
        files={"file": ("poster.png", image_bytes_png, "image/png")},
    )
    assert response.status_code == 400
