"""
Clerk session verification dependency for FastAPI.

Usage:
    @router.get("/protected")
    def protected_route(user_id: str = Depends(get_current_user_id)):
        ...

Every protected route gets the authenticated Clerk user's ID injected.
Unauthenticated requests are rejected with 401 — never 403, so ownership
information is never leaked to unauthenticated callers.
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

# Clerk JWKS URL — derived from the frontend API URL (instance-specific).
# Format: https://<clerk-frontend-api>/.well-known/jwks.json
# The frontend API domain is embedded in the publishable key after base64 decode,
# but Clerk also exposes it as <your-instance>.clerk.accounts.dev
# We configure it explicitly via CLERK_JWKS_URL in settings for clarity.
_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(
            settings.CLERK_JWKS_URL,
            cache_jwk_set=True,
            lifespan=3600,
        )
    return _jwks_client


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    FastAPI dependency — verifies the Clerk session JWT and returns the user ID.

    Raises HTTP 401 for:
    - Missing Authorization header
    - Expired token
    - Invalid signature
    - Missing 'sub' claim
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True},
        )

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
