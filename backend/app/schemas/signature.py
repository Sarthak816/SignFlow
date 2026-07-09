import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class SignerIn(BaseModel):
    """Input: one signer for a signature request."""
    identifier: str        # Aadhaar-linked mobile number
    display_name: str | None = None

    @field_validator("identifier")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        # Strip spaces/dashes and validate it looks like a 10-digit Indian mobile number
        cleaned = re.sub(r"[\s\-]", "", v)
        if not re.match(r"^[6-9]\d{9}$", cleaned):
            raise ValueError(
                "Please enter a valid 10-digit Aadhaar-linked mobile number."
            )
        return cleaned


class SignatureRequestCreate(BaseModel):
    """Input: create a signature request for an uploaded document."""
    document_id: uuid.UUID
    signer: SignerIn
    redirect_url: str | None = None


class SignerResponse(BaseModel):
    """One signer's details in the response."""
    signer_id: uuid.UUID
    setu_signer_id: str
    identifier: str
    display_name: str | None
    signer_url: str
    status: str

    model_config = {"from_attributes": True}


class SignatureRequestResponse(BaseModel):
    """Returned after creating a signature request."""
    signature_request_id: uuid.UUID
    setu_signature_id: str
    document_id: uuid.UUID
    status: str
    signers: list[SignerResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
