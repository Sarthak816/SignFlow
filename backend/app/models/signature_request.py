import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SignatureRequest(Base):
    """
    Represents a Setu signature request created for a document.

    Kept separate from Document so a document can theoretically be re-sent
    for signature (new row here) without a new upload — the schema supports
    one-to-many even though MVP usage is mostly one-to-one.

    Status mapping from Setu's enum → our internal enum:
      sign_initiated / sign_pending / sign_in_progress  →  pending
      sign_complete                                      →  signed
    Expired and failed states are set by our own logic.
    """

    __tablename__ = "signature_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The `id` returned by Setu after POST /api/signature.
    # Used in GET /api/signature/:id and GET /api/signature/:id/download/
    setu_signature_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )

    # Internal simplified status — see docstring for mapping from Setu's enum.
    # Valid values: pending | signed | expired | failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")

    # Where Setu redirects the signer after completing the signing flow.
    redirect_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Updated every time we refresh status from Setu.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to signers — one request has one or more signers.
    # MVP uses one signer; schema is ready for multi-signer (v1.x).
    signers: Mapped[list["Signer"]] = relationship(  # noqa: F821
        "Signer", back_populates="signature_request", cascade="all, delete-orphan"
    )
