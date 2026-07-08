import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    """
    Represents a PDF uploaded to SignFlow.

    A document exists independently of whether a signature request has been
    created for it — keeping upload and signature-request creation as two
    separate backend steps, matching the Setu API flow.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The `id` returned by Setu after POST /api/documents.
    # This is the value used in all subsequent Setu API calls.
    setu_document_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Clerk user ID of the authenticated owner who uploaded this document.
    # Every query on this table must filter by owner_id — this is the
    # row-level security boundary described in Security_and_Access_SignFlow.md.
    owner_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    original_filename: Mapped[str] = mapped_column(String, nullable=False)

    # Local disk path in MVP; will become an S3 key when storage is swapped.
    # Abstracted behind services/storage.py so this field never needs to change.
    file_path: Mapped[str] = mapped_column(String, nullable=False)

    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
