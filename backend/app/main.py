import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import upload, signature_status, download

# Configure logging to stdout so Render captures it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SignFlow API",
    description="Contract upload and e-signature platform powered by Setu Aadhaar eSign APIs",
    version="1.0.0",
)

# CORS — only the configured frontend origin is allowed.
# Never use allow_origins=["*"] on a backend that handles uploads and signature data.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(signature_status.router)
app.include_router(download.router)


# ── Global exception handler ──────────────────────────────────────────────────
# Catches any unhandled exception and returns a generic message.
# Stack traces and DB errors NEVER reach the browser (security + UX).
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback
    logger.error(
        "Unhandled exception on %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong. Please try again shortly."},
    )


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "ok"}


@app.get("/debug-setu", tags=["health"])
async def debug_setu():
    """Temporary: test Setu upload directly and return exact error."""
    import httpx
    from app.services.setu_client import _headers, _base
    fake_pdf = b"%PDF-1.4 test"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{_base()}/api/documents",
            headers=_headers(),
            data={"name": "test.pdf"},
            files={"document": ("test.pdf", fake_pdf, "application/pdf")},
        )
        return {
            "status_code": r.status_code,
            "response": r.text[:500],
            "headers_sent": dict(r.request.headers),
        }
