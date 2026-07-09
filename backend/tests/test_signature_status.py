"""
Tests for GET /api/signature-status/:id, GET /api/download/:id, GET /api/documents
Uses conftest.py for shared in-memory SQLite DB and auth override.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.models.signer import Signer
import tests.conftest  # ensure overrides are applied  # noqa: F401
from tests.conftest import TestingSession

client = TestClient(app)


# ── Seed helpers ──────────────────────────────────────────────────────────────

def _seed_pending():
    db = TestingSession()
    doc_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    signer_id = uuid.uuid4()
    doc = Document(
        id=doc_id, setu_document_id="setu-doc-123", owner_id="test-owner-id",
        original_filename="contract.pdf", file_path="/tmp/contract.pdf", file_size_bytes=1024,
    )
    sig_req = SignatureRequest(
        id=sig_id, document_id=doc_id, setu_signature_id="setu-sig-456",
        status="pending", updated_at=datetime.now(timezone.utc),
    )
    signer = Signer(
        id=signer_id, signature_request_id=sig_id, setu_signer_id="setu-signer-789",
        identifier="9876543210", signer_url="https://dg-sandbox.setu.co/sign/abc123", status="pending",
    )
    db.add_all([doc, sig_req, signer])
    db.commit()
    db.close()
    return str(sig_id)


def _seed_signed():
    db = TestingSession()
    doc_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    signer_id = uuid.uuid4()
    doc = Document(
        id=doc_id, setu_document_id="setu-doc-signed", owner_id="test-owner-id",
        original_filename="signed.pdf", file_path="/tmp/signed.pdf", file_size_bytes=2048,
    )
    sig_req = SignatureRequest(
        id=sig_id, document_id=doc_id, setu_signature_id="setu-sig-signed",
        status="signed", updated_at=datetime.now(timezone.utc),
    )
    signer = Signer(
        id=signer_id, signature_request_id=sig_id, setu_signer_id="setu-signer-signed",
        identifier="9876543210", signer_url="https://dg-sandbox.setu.co/sign/done",
        status="signed", signed_at=datetime.now(timezone.utc),
    )
    db.add_all([doc, sig_req, signer])
    db.commit()
    db.close()
    return str(sig_id)


# ── Signature status tests ────────────────────────────────────────────────────

def test_status_returns_pending_from_setu():
    sig_id = _seed_pending()
    setu_response = {
        "id": "setu-sig-456", "status": "sign_pending",
        "signers": [{"id": "setu-signer-789", "identifier": "9876543210", "status": "pending"}],
    }
    with patch("app.routers.signature_status.setu_client.get_signature_status",
               new_callable=AsyncMock, return_value=setu_response):
        response = client.get(f"/api/signature-status/{sig_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["refresh_failed"] is False


def test_status_returns_signed_from_setu():
    sig_id = _seed_pending()
    setu_response = {
        "id": "setu-sig-456", "status": "sign_complete",
        "signers": [{"id": "setu-signer-789", "identifier": "9876543210", "status": "signed"}],
    }
    with patch("app.routers.signature_status.setu_client.get_signature_status",
               new_callable=AsyncMock, return_value=setu_response):
        response = client.get(f"/api/signature-status/{sig_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "signed"


def test_status_returns_last_known_on_setu_failure():
    sig_id = _seed_pending()
    from app.services.setu_client import SetuAPIError
    with patch("app.routers.signature_status.setu_client.get_signature_status",
               new_callable=AsyncMock, side_effect=SetuAPIError("Setu down")):
        response = client.get(f"/api/signature-status/{sig_id}")
    assert response.status_code == 200
    assert response.json()["refresh_failed"] is True
    assert response.json()["status"] == "pending"


def test_status_404_for_wrong_owner():
    db = TestingSession()
    doc_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    db.add(Document(id=doc_id, setu_document_id="x", owner_id="other-owner",
                    original_filename="x.pdf", file_path="/tmp/x.pdf", file_size_bytes=1))
    db.add(SignatureRequest(id=sig_id, document_id=doc_id, setu_signature_id="sig-x",
                            status="pending", updated_at=datetime.now(timezone.utc)))
    db.commit(); db.close()
    response = client.get(f"/api/signature-status/{sig_id}")
    assert response.status_code == 404


def test_status_404_for_nonexistent():
    response = client.get(f"/api/signature-status/{uuid.uuid4()}")
    assert response.status_code == 404


# ── Download tests ────────────────────────────────────────────────────────────

def test_download_success_when_signed():
    sig_id = _seed_signed()
    fake_pdf = b"%PDF-1.4 signed content"
    with patch("app.routers.download.setu_client.download_document",
               new_callable=AsyncMock, return_value=fake_pdf):
        response = client.get(f"/api/download/{sig_id}")
    assert response.status_code == 200
    assert response.content == fake_pdf
    assert "application/pdf" in response.headers["content-type"]


def test_download_blocked_when_not_signed():
    sig_id = _seed_pending()
    response = client.get(f"/api/download/{sig_id}")
    assert response.status_code == 400
    assert "hasn't been signed" in response.json()["detail"]


def test_download_404_wrong_owner():
    db = TestingSession()
    doc_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    db.add(Document(id=doc_id, setu_document_id="y", owner_id="other-owner",
                    original_filename="y.pdf", file_path="/tmp/y.pdf", file_size_bytes=1))
    db.add(SignatureRequest(id=sig_id, document_id=doc_id, setu_signature_id="sig-y",
                            status="signed", updated_at=datetime.now(timezone.utc)))
    db.commit(); db.close()
    response = client.get(f"/api/download/{sig_id}")
    assert response.status_code == 404


def test_list_documents_returns_list():
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
