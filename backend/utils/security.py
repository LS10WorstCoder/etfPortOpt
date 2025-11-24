"""
Security utilities for Supabase authentication.
"""
from typing import Optional
from jose import JWTError, jwt
from config import settings

# JWT algorithm for Supabase tokens
ALGORITHM = "HS256"


def verify_supabase_token(token: str) -> Optional[dict]:
    """
    Verify a Supabase JWT token.
    
    Args:
        token: The JWT token from Supabase client
        
    Returns:
        Dictionary with user info if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            audience="authenticated"
        )
        return payload
    except JWTError:
        return None


def extract_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from Supabase token.
    
    Args:
        token: Supabase JWT token
        
    Returns:
        User UUID if valid, None otherwise
    """
    payload = verify_supabase_token(token)
    if payload:
        return payload.get("sub")  # Supabase uses 'sub' for user ID
    return None
