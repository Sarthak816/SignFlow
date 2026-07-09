"""
Unit tests for services/setu_client.py

All HTTP calls are mocked — no real Setu network calls made.
Tests verify request shape, response parsing, timeout handling,
and non-2xx error handling for all four functions.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.setu_client import (
    SetuAPIError,
    upload_document,
    create_signature_request,
    get_signature_status,
    download_document,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_client(get_side_effect=None, post_side_effect=None):
    """Return a patched AsyncClient context manager."""
    mock_client = AsyncMock()
    if get_side_effect is not None:
        mock_client.get = AsyncMock(side_effect=get_side_effect)
    if post_side_effect is not None:
        mock_client.post = AsyncMock(side_effect=post_side_effect)
    return mock_client


def _ok_response(body: dict):
    r = MagicMock()
    r.is_success = True
    r.json.return_value = body
    return r


def _err_response(status_code: int):
    r = MagicMock()
    r.is_success = False
    r.status_code = status_code
    return r


# ── upload_document ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_document_success():
    body = {"id": "setu-doc-123", "name": "contract.pdf"}

    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(post_side_effect=[_ok_response(body)])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await upload_document("contract.pdf", b"%PDF-fake")

    assert result["id"] == "setu-doc-123"
    # Verify multipart part name is "document" as Setu requires
    call_kwargs = mc.post.call_args.kwargs
    assert "document" in call_kwargs["files"]


@pytest.mark.asyncio
async def test_upload_document_timeout():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(post_side_effect=httpx.TimeoutException("timeout"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError) as exc:
            await upload_document("contract.pdf", b"%PDF-fake")

    assert "signing partner" in str(exc.value)


@pytest.mark.asyncio
async def test_upload_document_non_2xx():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(post_side_effect=[_err_response(400)])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError) as exc:
            await upload_document("contract.pdf", b"%PDF-fake")

    assert exc.value.status_code == 400


# ── create_signature_request ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_signature_request_success():
    body = {
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

    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(post_side_effect=[_ok_response(body)])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await create_signature_request(
            setu_document_id="setu-doc-123",
            redirect_url="http://localhost:3000/status",
            signers=[
                {
                    "identifier": "9876543210",
                    "signerNo": 1,
                    "signature": {
                        "onPages": "all",
                        "position": "bottom-right",
                        "height": 60,
                        "width": 180,
                    },
                }
            ],
        )

    assert result["id"] == "setu-sig-456"
    # Each signer has their own individual URL — not one shared link
    assert result["signers"][0]["url"] == "https://dg-sandbox.setu.co/sign/abc123"


@pytest.mark.asyncio
async def test_create_signature_request_timeout():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(post_side_effect=httpx.TimeoutException("timeout"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError):
            await create_signature_request("doc-id", "http://redir", [])


@pytest.mark.asyncio
async def test_create_signature_request_non_2xx():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(post_side_effect=[_err_response(422)])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError) as exc:
            await create_signature_request("doc-id", "http://redir", [])

    assert exc.value.status_code == 422


# ── get_signature_status ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_signature_status_success():
    body = {
        "documentId": "setu-doc-123",
        "id": "setu-sig-456",
        "status": "sign_complete",
        "signers": [
            {"id": "setu-signer-789", "identifier": "9876543210", "status": "signed"}
        ],
    }

    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(get_side_effect=[_ok_response(body)])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await get_signature_status("setu-sig-456")

    assert result["status"] == "sign_complete"
    assert result["signers"][0]["status"] == "signed"


@pytest.mark.asyncio
async def test_get_signature_status_timeout():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(get_side_effect=httpx.TimeoutException("timeout"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError):
            await get_signature_status("setu-sig-456")


# ── download_document ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_download_document_success():
    fake_pdf = b"%PDF-1.4 fake signed content"

    presigned_resp = _ok_response({
        "downloadUrl": "https://s3.amazonaws.com/bucket/signed.pdf?token=xyz",
        "id": "setu-sig-456",
        "validUpto": "2026-07-09T18:00:00Z",
    })

    pdf_resp = MagicMock()
    pdf_resp.is_success = True
    pdf_resp.content = fake_pdf

    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(get_side_effect=[presigned_resp, pdf_resp])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await download_document("setu-sig-456")

    assert result == fake_pdf
    # Two GET calls: first for presigned URL, second for actual PDF binary
    assert mc.get.call_count == 2


@pytest.mark.asyncio
async def test_download_document_presigned_fetch_fails():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(get_side_effect=[_err_response(404)])
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError) as exc:
            await download_document("setu-sig-456")

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_download_document_timeout():
    with patch("app.services.setu_client.httpx.AsyncClient") as MockClient:
        mc = _mock_client(get_side_effect=httpx.TimeoutException("timeout"))
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mc)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(SetuAPIError):
            await download_document("setu-sig-456")
