"""
Portfolio utility functions for reusable operations.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.portfolio import Portfolio
from models.holding import Holding
from models.user import User


def get_user_portfolio_or_404(
    portfolio_id: int,
    user: User,
    db: Session
) -> Portfolio:
    """Get portfolio if user owns it, else raise 404."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return portfolio


def get_portfolio_holdings_or_error(portfolio_id: int, db: Session) -> List[Holding]:
    """Get holdings or raise error if empty."""
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    if not holdings:
        raise HTTPException(status_code=400, detail="Portfolio has no holdings")
    return holdings
