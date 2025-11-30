"""
Authentication API endpoints using Supabase Auth.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from supabase import create_client, Client
from typing import Optional

from database import get_db
from models.user import User
from schemas.user import UserRegister, UserLogin, Token, UserResponse
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# HTTP Bearer for token extraction
security = HTTPBearer()

# Initialize Supabase client
def get_supabase() -> Client:
    """Get Supabase client instance"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from Supabase JWT token.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        supabase = get_supabase()
        # Verify token with Supabase
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        supabase_user = user_response.user
        
        # Get or create user in local database for portfolio relationships
        user = db.query(User).filter(User.email == supabase_user.email).first()
        if not user:
            user = User(
                id=supabase_user.id,  # Use Supabase user ID
                email=supabase_user.email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user account using Supabase Auth.
    
    Args:
        user_data: User registration data (email, password)
        
    Returns:
        JWT access token from Supabase
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        supabase = get_supabase()
        
        # Sign up with Supabase
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        return {
            "access_token": auth_response.session.access_token,
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
    Authenticate user with Supabase and return JWT token.
    
    Args:
        user_data: User login credentials (email, password)
        
    Returns:
        JWT access token from Supabase
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        supabase = get_supabase()
        
        # Sign in with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Args:
        current_user: Current user from Supabase JWT token
        
    Returns:
        User object
    """
    return current_user
