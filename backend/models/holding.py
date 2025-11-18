"""
Holding model - represents individual assets in a portfolio
"""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    average_cost = Column(Numeric(20, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    # Ensure unique ticker per portfolio
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'ticker', name='unique_portfolio_ticker'),
    )
    
    def __repr__(self):
        return f"<Holding {self.ticker} qty:{self.quantity}>"
