# Import all models here so SQLAlchemy registers them on Base.metadata.
# Alembic's env.py imports Base from app.database — these imports must run
# before autogenerate can detect the tables.
from app.models.document import Document
from app.models.signature_request import SignatureRequest
from app.models.signer import Signer

__all__ = ["Document", "SignatureRequest", "Signer"]
