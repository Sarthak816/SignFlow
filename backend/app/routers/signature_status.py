"""
GET /api/signature-status/:id  — fetch live status from Setu, update DB.

Security:
- Route requires authentication (Clerk JWT)
- Returns 404 (never 403) if the signature_request doesn't belong to the
  authenticated user — ownership is not leaked to unauthenticated callers

Resilience:
- If the Setu call fails, returns the last known local status with a flag
  indicating the live refresh failed and when data was last good
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.models.signer import Signer
from app.services import setu_client
from app.services.setu_client import SetuAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["status"])

# Setu request-level status → our internal enum
SETU_STATUS_MAP = {
    "sign_initiated": "pending",
    "sign_pending": "pending",
    "sign_in_progress": "pending",
    "sign_complete": "signed",
}


class SignerStatusResponse(BaseModel):
    setu_signer_id: str
    identifier: str
    display_name: str | None
    status: str
    signed_at: datetime | None
    signer_url: str


class SignatureStatusResponse(BaseModel):
    signature_request_id: str
    setu_signature_id: str
    document_id: str
    original_filename: str
    status: str
    signers: list[SignerStatusResponse]
    updated_at: datetime
    refresh_failed: bool = False
    last_refreshed_at: datetime | None = None


@router.get(
    "/signature-status/{signature_request_id}",
    response_model=SignatureStatusResponse,
    summary="Get signature request status (refreshed live from Setu)",
)
async def get_signature_status(
    signature_request_id: str,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    # ── Fetch the signature request and verify ownership ──────────────────────
    import uuid as _uuid
    try:
        sig_uuid = _uuid.UUID(signature_request_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Signature request not found.")

    sig_req = (
        db.query(SignatureRequest)
        .filter(SignatureRequest.id == sig_uuid)
        .first()
    )
    if not sig_req:
        raise HTTPException(status_code=404, detail="Signature request not found.")

    # Verify ownership through the parent document — return 404, not 403
    doc = db.query(Document).filter(
        Document.id == sig_req.document_id,
        Document.owner_id == owner_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Signature request not found.")

    signers = db.query(Signer).filter(
        Signer.signature_request_id == sig_req.id
    ).all()

    refresh_failed = False

    # ── Live refresh from Setu ────────────────────────────────────────────────
    try:
        setu_data = await setu_client.get_signature_status(sig_req.setu_signature_id)

        # Map Setu's status to our internal enum
        raw_status = setu_data.get("status", "")
        new_status = SETU_STATUS_MAP.get(raw_status, sig_req.status)
        sig_req.status = new_status
        sig_req.updated_at = datetime.now(timezone.utc)

        # Update per-signer status
        setu_signers_map = {s["id"]: s for s in setu_data.get("signers", [])}
        for signer in signers:
            setu_signer = setu_signers_map.get(signer.setu_signer_id)
            if setu_signer:
                new_signer_status = setu_signer.get("status", signer.status)
                if new_signer_status == "signed" and signer.signed_at is None:
                    signer.signed_at = datetime.now(timezone.utc)
                signer.status = new_signer_status

        db.commit()
        db.refresh(sig_req)
        for s in signers:
            db.refresh(s)

    except SetuAPIError as e:
        # Setu call failed — return last known data with refresh_failed flag
        logger.warning("Setu status refresh failed for %s: %s", sig_req.setu_signature_id, e)
        refresh_failed = True

    return SignatureStatusResponse(
        signature_request_id=str(sig_req.id),
        setu_signature_id=sig_req.setu_signature_id,
        document_id=str(sig_req.document_id),
        original_filename=doc.original_filename,
        status=sig_req.status,
        signers=[
            SignerStatusResponse(
                setu_signer_id=s.setu_signer_id,
                identifier=s.identifier,
                display_name=s.display_name,
                status=s.status,
                signed_at=s.signed_at,
                signer_url=s.signer_url,
            )
            for s in signers
        ],
        updated_at=sig_req.updated_at,
        refresh_failed=refresh_failed,
        last_refreshed_at=sig_req.updated_at if not refresh_failed else None,
    )


@router.get(
    "/documents",
    summary="List all signature requests for the authenticated user",
)
async def list_documents(
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """Returns all documents + their latest signature request for the dashboard."""
    docs = db.query(Document).filter(Document.owner_id == owner_id).all()

    result = []
    for doc in docs:
        sig_req = (
            db.query(SignatureRequest)
            .filter(SignatureRequest.document_id == doc.id)
            .order_by(SignatureRequest.created_at.desc())
            .first()
        )
        signers = []
        if sig_req:
            signers = db.query(Signer).filter(
                Signer.signature_request_id == sig_req.id
            ).all()

        result.append({
            "document_id": str(doc.id),
            "original_filename": doc.original_filename,
            "uploaded_at": doc.uploaded_at,
            "signature_request_id": str(sig_req.id) if sig_req else None,
            "setu_signature_id": sig_req.setu_signature_id if sig_req else None,
            "status": sig_req.status if sig_req else "no_request",
            "updated_at": sig_req.updated_at if sig_req else None,
            "signers": [
                {
                    "identifier": s.identifier,
                    "display_name": s.display_name,
                    "status": s.status,
                    "signer_url": s.signer_url,
                    "signed_at": s.signed_at,
                }
                for s in signers
            ],
        })

    return result
