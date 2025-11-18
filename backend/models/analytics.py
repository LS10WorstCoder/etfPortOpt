"""
Portfolio analytics cache model
"""

from sqlalchemy import Column, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class PortfolioAnalytics(Base):
    __tablename__ = "portfolio_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    calculation_date = Column(Date, nullable=False)
    total_value = Column(Numeric(20, 2))
    daily_return = Column(Numeric(10, 6))
    volatility = Column(Numeric(10, 6))
    sharpe_ratio = Column(Numeric(10, 6))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure unique calculation per portfolio per date
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'calculation_date', name='unique_portfolio_date'),
    )
    
    def __repr__(self):
        return f"<PortfolioAnalytics {self.portfolio_id} {self.calculation_date}>"
