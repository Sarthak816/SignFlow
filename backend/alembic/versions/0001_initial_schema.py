"""initial schema: documents, signature_requests, signers

Revision ID: 0001
Revises:
Create Date: 2026-07-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── documents ────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("setu_document_id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_setu_document_id", "documents", ["setu_document_id"])

    # ── signature_requests ───────────────────────────────────────────────────
    op.create_table(
        "signature_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("setu_signature_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("redirect_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_signature_requests_document_id", "signature_requests", ["document_id"]
    )
    op.create_index(
        "ix_signature_requests_setu_signature_id",
        "signature_requests",
        ["setu_signature_id"],
    )

    # ── signers ───────────────────────────────────────────────────────────────
    op.create_table(
        "signers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "signature_request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("signature_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("setu_signer_id", sa.String(), nullable=False),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("signer_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_signers_signature_request_id", "signers", ["signature_request_id"]
    )


def downgrade() -> None:
    op.drop_table("signers")
    op.drop_table("signature_requests")
    op.drop_table("documents")
