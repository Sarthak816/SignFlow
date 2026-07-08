def validate_pdf(file_bytes: bytes, filename: str, max_size_mb: int) -> str | None:
    """
    Validate that the uploaded file is a genuine PDF within the size limit.

    Returns an error message string if validation fails, or None if the file is valid.

    Checks:
    - File size against max_size_mb
    - PDF magic bytes (%PDF-) to confirm actual content type, not just extension
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    if len(file_bytes) > max_size_bytes:
        return (
            f"This file is {len(file_bytes) // (1024 * 1024)}MB — "
            f"the limit is {max_size_mb}MB. Choose a smaller PDF."
        )

    # Check PDF magic bytes — the file must start with %PDF-
    # A file renamed to .pdf but containing other content will fail here.
    if not file_bytes.startswith(b"%PDF-"):
        return "This file is not a valid PDF. Please upload a PDF document."

    return None
