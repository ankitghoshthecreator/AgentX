from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# For Phase 2 prototype, we use static API keys.
# In a real enterprise system (Phase 3), this would integrate with OAuth2 / JWT / Auth0.
VALID_TOKENS = {
    "admin-secret-token-123": "admin_user",
    "test-token-456": "test_user"
}

def verify_token(token: str) -> str:
    """Verify bearer token and return the username."""
    if token not in VALID_TOKENS:
        logger.warning(f"Failed authentication attempt with token: {token[:5]}...")
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    
    return VALID_TOKENS[token]
