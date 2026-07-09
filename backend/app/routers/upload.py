"""
POST /api/upload-contract  — upload a PDF and create a signature request.

Flow:
  1. Validate file (magic bytes + size)
  2. Save to local disk via storage.save_file
  3. Call setu_client.upload_document → get setu_document_id
  4. Write documents row (owner_id = authenticated user)
  5. Call setu_client.create_signature_request → get signatureId + signerUrl
  6. Write signature_requests + signers rows
  7. Return combined response

If the Setu upload (step 3) fails after the file is already saved (step 2),
the documents row is still created with status "upload_failed" so nothing is
silently lost and the user can retry without re-uploading.

If the signature request creation (step 5) fails after the document row
exists, the document row remains and the error is surfaced clearly.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.models.signer import Signer
from app.schemas.document import DocumentResponse
from app.schemas.signature import SignatureRequestResponse, SignerResponse
from app.services import setu_client, storage
from app.services.setu_client import SetuAPIError
from app.utils.validators import validate_pdf

router = APIRouter(prefix="/api", tags=["upload"])


class UploadContractResponse(DocumentResponse):
    """Extended response that includes the signature request created in the same call."""
    signature_request_id: uuid.UUID
    setu_signature_id: str
    status: str
    signer_url: str
    setu_document_id: str


@router.post(
    "/upload-contract",
    response_model=UploadContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF contract and create a signature request",
)
async def upload_contract(
    file: UploadFile = File(..., description="PDF file to upload"),
    signer_identifier: str = Form(..., description="Aadhaar-linked mobile number of the signer"),
    signer_display_name: str = Form(None, description="Signer's display name (optional)"),
    redirect_url: str = Form(None, description="URL to redirect signer after signing"),
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    # ── 1. Read and validate the uploaded file ────────────────────────────────
    file_bytes = await file.read()
    filename = file.filename or "document.pdf"

    error = validate_pdf(file_bytes, filename, settings.MAX_UPLOAD_SIZE_MB)
    if error:
        raise HTTPException(status_code=422, detail=error)

    # ── 2. Validate signer mobile number ──────────────────────────────────────
    import re
    cleaned_identifier = re.sub(r"[\s\-]", "", signer_identifier)
    if not re.match(r"^[6-9]\d{9}$", cleaned_identifier):
        raise HTTPException(
            status_code=422,
            detail="Please enter a valid 10-digit Aadhaar-linked mobile number.",
        )

    # ── 3. Save file to disk ──────────────────────────────────────────────────
    file_path = storage.save_file(file_bytes, filename)

    # ── 4. Upload document to Setu ────────────────────────────────────────────
    try:
        setu_doc = await setu_client.upload_document(filename, file_bytes)
    except SetuAPIError as e:
        # File saved but Setu upload failed — persist document row with failure note
        doc = Document(
            id=uuid.uuid4(),
            setu_document_id="upload_failed",
            owner_id=owner_id,
            original_filename=filename,
            file_path=file_path,
            file_size_bytes=len(file_bytes),
        )
        db.add(doc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    setu_document_id: str = setu_doc["id"]

    # ── 5. Persist document row ───────────────────────────────────────────────
    doc = Document(
        id=uuid.uuid4(),
        setu_document_id=setu_document_id,
        owner_id=owner_id,
        original_filename=filename,
        file_path=file_path,
        file_size_bytes=len(file_bytes),
    )
    db.add(doc)
    db.flush()  # get doc.id without committing yet

    # ── 6. Create signature request on Setu ───────────────────────────────────
    effective_redirect = redirect_url or f"{settings.FRONTEND_URL}/status"

    signers_payload = [
        {
            "identifier": cleaned_identifier,
            "signerNo": 1,
            "signature": {
                "onPages": "all",
                "position": "bottom-right",
                "height": 60,
                "width": 180,
            },
            **({"displayName": signer_display_name} if signer_display_name else {}),
        }
    ]

    try:
        setu_sig = await setu_client.create_signature_request(
            setu_document_id=setu_document_id,
            redirect_url=effective_redirect,
            signers=signers_payload,
        )
    except SetuAPIError as e:
        # Document row exists — commit it so data is not lost, then surface error
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    setu_signature_id: str = setu_sig["id"]
    setu_signers: list[dict] = setu_sig.get("signers", [])

    # ── 7. Persist signature_requests row ────────────────────────────────────
    sig_req = SignatureRequest(
        id=uuid.uuid4(),
        document_id=doc.id,
        setu_signature_id=setu_signature_id,
        status="pending",
        redirect_url=effective_redirect,
    )
    db.add(sig_req)
    db.flush()

    # ── 8. Persist signers rows ───────────────────────────────────────────────
    signer_rows: list[Signer] = []
    for s in setu_signers:
        signer_row = Signer(
            id=uuid.uuid4(),
            signature_request_id=sig_req.id,
            setu_signer_id=s["id"],
            identifier=s.get("identifier", cleaned_identifier),
            display_name=s.get("displayName") or signer_display_name,
            signer_url=s["url"],
            status=s.get("status", "pending"),
        )
        db.add(signer_row)
        signer_rows.append(signer_row)

    db.commit()
    db.refresh(doc)
    db.refresh(sig_req)

    # ── 9. Build response ─────────────────────────────────────────────────────
    first_signer_url = signer_rows[0].signer_url if signer_rows else ""

    return UploadContractResponse(
        document_id=doc.id,
        setu_document_id=doc.setu_document_id,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        uploaded_at=doc.uploaded_at,
        signature_request_id=sig_req.id,
        setu_signature_id=sig_req.setu_signature_id,
        status=sig_req.status,
        signer_url=first_signer_url,
    )
