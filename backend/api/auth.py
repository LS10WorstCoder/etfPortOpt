"""
Authentication API endpoints using Supabase.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from supabase import create_client, Client
from typing import Optional

from database import get_db
from models.user import User
from schemas.user import UserRegister, UserLogin, Token, UserResponse
from utils.security import verify_supabase_token, extract_user_id
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# HTTP Bearer scheme for token extraction
security = HTTPBearer()

# Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from Supabase token.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify Supabase token
    user_id = extract_user_id(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create user in local database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Create local user record from Supabase user
        try:
            supabase_user = supabase.auth.get_user(token)
            user = User(
                id=user_id,
                email=supabase_user.user.email,
                hashed_password="",  # Not needed with Supabase
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not retrieve user information"
            )
    
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user via Supabase.
    
    Args:
        user_data: User registration data (email, password)
        
    Returns:
        JWT access token from Supabase
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Register user with Supabase
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Email may already be registered."
            )
        
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    Authenticate user via Supabase and return JWT token.
    
    Args:
        user_data: User login credentials (email, password)
        
    Returns:
        JWT access token from Supabase
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        User object
    """
    return current_user
