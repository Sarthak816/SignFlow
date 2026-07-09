import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Returned after a successful document upload."""
    document_id: uuid.UUID
    setu_document_id: str
    original_filename: str
    file_size_bytes: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
