"""
Pydantic schemas for CSV import/export operations.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


class HoldingCSVRow(BaseModel):
    """Schema for a single holding row in CSV format."""
    ticker: str = Field(min_length=1, max_length=10)
    quantity: Decimal = Field(gt=0)
    average_cost: Optional[Decimal] = Field(None, ge=0)
    
    @field_validator('ticker')
    def ticker_uppercase(cls, v):
        """Convert ticker to uppercase."""
        return v.upper().strip()


class CSVImportResponse(BaseModel):
    """Response schema for CSV import operation."""
    success: bool
    total_rows: int
    imported: int
    skipped: int
    errors: list[str]
    holdings: list[dict]
