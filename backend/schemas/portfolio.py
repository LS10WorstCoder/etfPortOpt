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
    account_type: str = Field(
        default='taxable',
        pattern="^(taxable|roth_ira|traditional_ira|401k)$",
        description="Account type: taxable, roth_ira, traditional_ira, or 401k"
    )


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    account_type: Optional[str] = Field(
        None,
        pattern="^(taxable|roth_ira|traditional_ira|401k)$",
        description="Account type: taxable, roth_ira, traditional_ira, or 401k"
    )


class PortfolioResponse(BaseModel):
    """Schema for portfolio data in responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    account_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
