"""
Pydantic schemas for holding-related requests and responses.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal
import uuid


class HoldingCreate(BaseModel):
    """Schema for creating a new holding."""
    ticker: str = Field(min_length=1, max_length=10)
    quantity: Decimal = Field(gt=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)
    
    @field_validator('ticker')
    def ticker_uppercase(cls, v):
        """Convert ticker to uppercase."""
        return v.upper().strip()


class HoldingUpdate(BaseModel):
    """Schema for updating a holding."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)


class HoldingResponse(BaseModel):
    """Schema for holding data in responses."""
    id: uuid.UUID
    portfolio_id: uuid.UUID
    ticker: str
    quantity: Decimal
    average_cost: Optional[Decimal]
    created_at: datetime
    
    class Config:
        from_attributes = True
