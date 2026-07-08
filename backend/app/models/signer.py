import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Signer(Base):
    """
    Represents one signer on a signature request.

    Even though MVP supports one signer per document, this is a separate table
    because Setu returns one URL and one status per signer — not per request.
    Multi-signer support (v1.x) becomes "add more rows," not a schema redesign.

    Per Frontend_Specification_SignFlow.md Section 7.1:
    - `identifier` is an Aadhaar-linked mobile number, NOT an email address.
      Setu's eSign is Aadhaar OTP-based; identity is verified by phone number.
    - `signer_url` is this signer's individual signing link (each signer gets
      their own URL from Setu, not one shared link per request).
    - Per-signer status mirrors Setu's enum directly: pending | in_progress | signed
    """

    __tablename__ = "signers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    signature_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("signature_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Setu's own ID for this signer, returned inside the signers array.
    # Needed to match status updates back to the correct signer row.
    setu_signer_id: Mapped[str] = mapped_column(String, nullable=False)

    # Aadhaar-linked mobile number — this is how Setu identifies the signer.
    identifier: Mapped[str] = mapped_column(String, nullable=False)

    # Signer's display name — passed to Setu and optionally validated against
    # Aadhaar OTP data. Setu will block signing on a mismatch if this is set.
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)

    # This signer's individual signing link returned by Setu.
    signer_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Mirrors Setu's per-signer status enum: pending | in_progress | signed
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")

    # Filled in when our backend observes status flipping to "signed".
    # Setu doesn't return a literal signed_at timestamp, so we store the
    # time our backend first saw the signed state.
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Back-reference to the parent signature request.
    signature_request: Mapped["SignatureRequest"] = relationship(  # noqa: F821
        "SignatureRequest", back_populates="signers"
    )
