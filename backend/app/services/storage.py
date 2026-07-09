"""
File storage abstraction.

Local disk for MVP. To swap to S3-compatible storage later,
change only this file — no other code needs to change.
"""

import os
import uuid
from pathlib import Path

# Base upload directory — excluded from git via .gitignore
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_file(file_bytes: bytes, filename: str) -> str:
    """
    Save file_bytes to disk under a UUID-based filename.

    Returns the file path string (stored in documents.file_path).
    Using a UUID prefix prevents filename collisions and avoids
    exposing original filenames in the filesystem.
    """
    _ensure_upload_dir()
    unique_name = f"{uuid.uuid4()}_{filename}"
    file_path = UPLOAD_DIR / unique_name
    file_path.write_bytes(file_bytes)
    return str(file_path)


def delete_file(file_path: str) -> None:
    """Delete a stored file. Silently ignores missing files."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass
