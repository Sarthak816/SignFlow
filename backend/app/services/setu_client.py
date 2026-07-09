"""
Setu Aadhaar eSign API client.

This is the ONLY file in the entire codebase that references Setu credentials.
Credentials are injected from app.config.settings — never hardcoded, never
passed to any other module, never returned in any API response.

All four Setu API calls are wrapped here:
  1. upload_document           — POST /api/documents
  2. create_signature_request  — POST /api/signature
  3. get_signature_status      — GET  /api/signature/:id
  4. download_document         — GET  /api/signature/:id/download/

Every call has a 15-second timeout and raises SetuAPIError on timeout or
non-2xx response, per Security_and_Access_SignFlow.md Section 4.

NOTE: If any request/response shape here does not match your actual Setu
sandbox responses, stop and report the discrepancy — do not adapt silently.
"""

import httpx

from app.config import settings


class SetuAPIError(Exception):
    """Raised when a Setu API call fails or times out."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> dict[str, str]:
    """
    Build Setu auth headers. These three values never leave this file.
    Grep the rest of the codebase for SETU_CLIENT_ID / SETU_CLIENT_SECRET /
    SETU_PRODUCT_INSTANCE_ID — you should find zero matches outside this file.
    """
    return {
        "x-client-id": settings.SETU_CLIENT_ID,
        "x-client-secret": settings.SETU_CLIENT_SECRET,
        "x-product-instance-id": settings.SETU_PRODUCT_INSTANCE_ID,
    }


def _base() -> str:
    return settings.SETU_BASE_URL.rstrip("/")


async def upload_document(filename: str, file_bytes: bytes) -> dict:
    """
    Upload a PDF to Setu.

    POST /api/documents
    Multipart body:
      - payload: JSON string  {"name": "<filename>"}
      - files:   PDF binary   part name = "document"

    Response: {"id": "<setu_document_id>", "name": "<filename>"}
    The "id" is stored as documents.setu_document_id.
    """
    url = f"{_base()}/api/documents"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers=_headers(),
                # Setu expects `name` as a plain form field and `document` as the file part.
                # The spec doc showing `payload` as a JSON string is incorrect —
                # verified against the live sandbox: Format 3 (name direct + document key) returns 201.
                data={"name": filename},
                files={"document": (filename, file_bytes, "application/pdf")},
            )
    except httpx.TimeoutException:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )
    except httpx.RequestError:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )

    if not response.is_success:
        raise SetuAPIError(
            "Document upload failed. Please try again.",
            status_code=response.status_code,
        )

    return response.json()


async def create_signature_request(
    setu_document_id: str,
    redirect_url: str,
    signers: list[dict],
) -> dict:
    """
    Create a signature request on Setu.

    POST /api/signature
    Body: {
      "documentId": "<setu_document_id>",
      "redirectUrl": "<url>",
      "signers": [
        {
          "identifier": "<aadhaar-linked-mobile>",   ← mobile number, NOT email
          "displayName": "<optional>",
          "birthYear": "<optional>",
          "signerNo": 1,
          "signature": {
            "onPages": "all",
            "position": "bottom-right",
            "height": 60,
            "width": 180
          }
        }
      ]
    }

    Response:
      {
        "documentId": "...",
        "id": "<setu_signature_id>",    ← stored as signature_requests.setu_signature_id
        "redirectUrl": "...",
        "status": "sign_initiated",
        "signers": [
          {
            "id": "<setu_signer_id>",
            "identifier": "...",
            "displayName": "...",
            "status": "pending",
            "url": "<signing_link>"     ← stored as signers.signer_url (one per signer)
          }
        ]
      }
    """
    url = f"{_base()}/api/signature"

    payload = {
        "documentId": setu_document_id,
        "redirectUrl": redirect_url,
        "signers": signers,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers={**_headers(), "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.TimeoutException:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )
    except httpx.RequestError:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )

    if not response.is_success:
        raise SetuAPIError(
            "Signature request creation failed. Please try again.",
            status_code=response.status_code,
        )

    return response.json()


async def get_signature_status(setu_signature_id: str) -> dict:
    """
    Fetch the latest signature status from Setu.

    GET /api/signature/:id

    Response:
      {
        "documentId": "...",
        "id": "...",
        "status": "sign_initiated|sign_pending|sign_in_progress|sign_complete",
        "signers": [
          {
            "id": "...",
            "identifier": "...",
            "status": "pending|in_progress|signed",
            "signatureDetails": {...}    ← optional, present when signed
          }
        ]
      }

    Setu → internal status mapping (applied in the router, not here):
      sign_initiated | sign_pending | sign_in_progress  →  pending
      sign_complete                                      →  signed
    """
    url = f"{_base()}/api/signature/{setu_signature_id}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=_headers())
    except httpx.TimeoutException:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )
    except httpx.RequestError:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )

    if not response.is_success:
        raise SetuAPIError(
            "Status check failed. Please try again.",
            status_code=response.status_code,
        )

    return response.json()


async def download_document(setu_signature_id: str) -> bytes:
    """
    Download the signed document from Setu.

    GET /api/signature/:id/download/
    Uses setu_signature_id — NOT the document id (per spec).

    Setu response: {"downloadUrl": "<presigned_url>", "id": "...", "validUpto": "..."}

    This function:
      1. Fetches the presigned URL from Setu
      2. Fetches the actual PDF binary from that presigned URL server-side
      3. Returns the raw PDF bytes to the caller

    The raw downloadUrl is NEVER passed to the frontend.
    Only the binary content is streamed back, preserving the
    "frontend never talks to Setu" security boundary.
    """
    url = f"{_base()}/api/signature/{setu_signature_id}/download/"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: get the presigned URL from Setu
            meta_response = await client.get(url, headers=_headers())

            if not meta_response.is_success:
                raise SetuAPIError(
                    "Download failed. Please try again.",
                    status_code=meta_response.status_code,
                )

            data = meta_response.json()
            download_url: str = data["downloadUrl"]

            # Step 2: fetch the actual PDF binary from the presigned URL
            # No Setu auth headers on the presigned URL itself
            pdf_response = await client.get(download_url, timeout=30.0)

            if not pdf_response.is_success:
                raise SetuAPIError(
                    "Download failed. Please try again.",
                    status_code=pdf_response.status_code,
                )

            return pdf_response.content

    except SetuAPIError:
        raise
    except httpx.TimeoutException:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )
    except httpx.RequestError:
        raise SetuAPIError(
            "We couldn't reach our signing partner right now — please try again in a few minutes."
        )
