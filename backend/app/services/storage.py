"""
File storage abstraction.

Uses /tmp for cloud deployments (Render/Railway) where the app directory
is read-only. For local dev, also uses /tmp to keep things consistent.

To swap to S3-compatible storage later, change only this file.
"""

import uuid
import tempfile
from pathlib import Path


def save_file(file_bytes: bytes, filename: str) -> str:
    """
    Save file_bytes to a temp directory.

    Returns the file path string (stored in documents.file_path).
    Using a UUID prefix prevents filename collisions.
    """
    tmp_dir = Path(tempfile.gettempdir()) / "signflow_uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4()}_{filename}"
    file_path = tmp_dir / unique_name
    file_path.write_bytes(file_bytes)
    return str(file_path)


def delete_file(file_path: str) -> None:
    """Delete a stored file. Silently ignores missing files."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass
