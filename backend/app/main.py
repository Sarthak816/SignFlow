from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="SignFlow API",
    description="Contract upload and e-signature platform powered by Setu Aadhaar eSign APIs",
    version="1.0.0",
)

# CORS — only the configured frontend origin is allowed.
# Never use allow_origins=["*"] on a backend that handles file uploads and signature data.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for deployment monitoring and uptime verification."""
    return {"status": "ok"}
