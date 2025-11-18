"""
Optimization results cache model
"""

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid


class OptimizationResult(Base):
    __tablename__ = "optimization_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    strategy = Column(String(50), nullable=False)
    optimized_weights = Column(JSONB, nullable=False)
    expected_return = Column(Numeric(10, 6))
    expected_volatility = Column(Numeric(10, 6))
    sharpe_ratio = Column(Numeric(10, 6))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<OptimizationResult {self.strategy} sharpe:{self.sharpe_ratio}>"
