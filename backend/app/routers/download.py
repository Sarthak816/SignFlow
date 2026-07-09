"""
GET /api/download/:id  — stream the signed PDF through the backend.

The raw Setu downloadUrl is NEVER returned to the frontend.
The backend fetches it and streams the binary back directly.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.services import setu_client
from app.services.setu_client import SetuAPIError

router = APIRouter(prefix="/api", tags=["download"])


@router.get(
    "/download/{signature_request_id}",
    summary="Download the signed PDF (proxied through backend)",
    response_class=Response,
)
async def download_signed_document(
    signature_request_id: str,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    # ── Fetch and verify ownership ────────────────────────────────────────────
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

    doc = db.query(Document).filter(
        Document.id == sig_req.document_id,
        Document.owner_id == owner_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Signature request not found.")

    # ── Guard: only allow download when signed ────────────────────────────────
    if sig_req.status != "signed":
        raise HTTPException(
            status_code=400,
            detail="This document hasn't been signed yet.",
        )

    # ── Fetch binary from Setu and stream back ────────────────────────────────
    try:
        pdf_bytes = await setu_client.download_document(sig_req.setu_signature_id)
    except SetuAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    safe_filename = doc.original_filename.replace('"', "")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
        },
    )
