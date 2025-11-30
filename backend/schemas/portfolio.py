"""
Pydantic schemas for portfolio-related requests and responses.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class PortfolioCreate(BaseModel):
    """Schema for creating a new portfolio."""
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    """Schema for portfolio data in responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
