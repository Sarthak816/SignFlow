def validate_pdf(file_bytes: bytes, filename: str, max_size_mb: int) -> str | None:
    """
    Validate that the uploaded file is a genuine PDF within the size limit.

    Returns an error message string if validation fails, or None if valid.

    Checks:
    1. File size against max_size_mb
    2. PDF magic bytes (%PDF-) — validates actual content, not just extension.
       A file renamed to .pdf but containing other content will fail here.
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    if len(file_bytes) > max_size_bytes:
        actual_mb = round(len(file_bytes) / (1024 * 1024), 1)
        return (
            f"This file is {actual_mb}MB — the limit is {max_size_mb}MB. "
            f"Choose a smaller PDF."
        )

    if not file_bytes.startswith(b"%PDF-"):
        return "This file is not a valid PDF. Please upload a PDF document."

    return None
