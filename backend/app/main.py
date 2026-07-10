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


@app.get("/debug-config", tags=["health"])
def debug_config():
    """Temporary: verify env vars loaded correctly on Render. Remove after fix."""
    return {
        "setu_client_id_prefix": settings.SETU_CLIENT_ID[:8] if settings.SETU_CLIENT_ID else "MISSING",
        "setu_secret_len": len(settings.SETU_CLIENT_SECRET),
        "setu_product_id_prefix": settings.SETU_PRODUCT_INSTANCE_ID[:8] if settings.SETU_PRODUCT_INSTANCE_ID else "MISSING",
        "setu_base_url": settings.SETU_BASE_URL,
        "environment": settings.ENVIRONMENT,
    }
