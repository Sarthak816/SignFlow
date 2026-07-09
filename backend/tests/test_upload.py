"""
Tests for POST /api/upload-contract
Uses conftest.py for shared in-memory SQLite DB and auth override.
"""

import io
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_current_user_id
import tests.conftest  # ensure overrides are applied  # noqa: F401

client = TestClient(app)

FAKE_PDF = b"%PDF-1.4 fake content"
SETU_DOC_RESPONSE = {"id": "setu-doc-123", "name": "test.pdf"}
SETU_SIG_RESPONSE = {
    "documentId": "setu-doc-123",
    "id": "setu-sig-456",
    "redirectUrl": "http://localhost:3000/status",
    "status": "sign_initiated",
    "signers": [
        {
            "id": "setu-signer-789",
            "identifier": "9876543210",
            "displayName": "Test User",
            "status": "pending",
            "url": "https://dg-sandbox.setu.co/sign/abc123",
        }
    ],
}


def _upload(file_bytes=FAKE_PDF, signer="9876543210", display_name=None):
    data = {"signer_identifier": signer}
    if display_name:
        data["signer_display_name"] = display_name
    return client.post(
        "/api/upload-contract",
        files={"file": ("test.pdf", io.BytesIO(file_bytes), "application/pdf")},
        data=data,
    )


def test_upload_contract_success():
    with (
        patch("app.routers.upload.setu_client.upload_document", new_callable=AsyncMock, return_value=SETU_DOC_RESPONSE),
        patch("app.routers.upload.setu_client.create_signature_request", new_callable=AsyncMock, return_value=SETU_SIG_RESPONSE),
        patch("app.routers.upload.storage.save_file", return_value="/tmp/fake.pdf"),
    ):
        response = _upload()

    assert response.status_code == 201
    body = response.json()
    assert body["setu_document_id"] == "setu-doc-123"
    assert body["setu_signature_id"] == "setu-sig-456"
    assert body["status"] == "pending"
    assert body["signer_url"] == "https://dg-sandbox.setu.co/sign/abc123"


def test_upload_rejects_non_pdf():
    response = _upload(file_bytes=b"not a pdf at all")
    assert response.status_code == 422
    assert "valid PDF" in response.json()["detail"]


def test_upload_rejects_oversized_file():
    big_file = b"%PDF-" + b"x" * (11 * 1024 * 1024)
    response = _upload(file_bytes=big_file)
    assert response.status_code == 422
    assert "limit" in response.json()["detail"]


def test_upload_rejects_invalid_mobile():
    response = _upload(signer="1234")
    assert response.status_code == 422
    assert "mobile" in response.json()["detail"].lower()


def test_upload_setu_upload_fails_returns_502():
    from app.services.setu_client import SetuAPIError
    with (
        patch("app.routers.upload.setu_client.upload_document", new_callable=AsyncMock, side_effect=SetuAPIError("Setu down")),
        patch("app.routers.upload.storage.save_file", return_value="/tmp/fake.pdf"),
    ):
        response = _upload()
    assert response.status_code == 502


def test_upload_setu_sig_fails_returns_502():
    from app.services.setu_client import SetuAPIError
    with (
        patch("app.routers.upload.setu_client.upload_document", new_callable=AsyncMock, return_value=SETU_DOC_RESPONSE),
        patch("app.routers.upload.setu_client.create_signature_request", new_callable=AsyncMock, side_effect=SetuAPIError("Setu down")),
        patch("app.routers.upload.storage.save_file", return_value="/tmp/fake.pdf"),
    ):
        response = _upload()
    assert response.status_code == 502


def test_upload_requires_auth():
    del app.dependency_overrides[get_current_user_id]
    try:
        response = _upload()
        assert response.status_code == 401
    finally:
        from tests.conftest import override_auth
        app.dependency_overrides[get_current_user_id] = override_auth
