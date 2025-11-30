"""
Holdings API endpoints for managing portfolio holdings.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from database import get_db
from models.user import User
from models.holding import Holding
from schemas.holding import HoldingCreate, HoldingUpdate, HoldingResponse
from api.auth import get_current_user
from services.market_data import MarketDataService
from utils.portfolio_utils import get_user_portfolio_or_404

router = APIRouter(prefix="/portfolios/{portfolio_id}/holdings", tags=["Holdings"])

MAX_HOLDINGS = 100  # Maximum holdings per portfolio


def _get_holding_or_404(holding_id: str, portfolio_id: str, db: Session) -> Holding:
    """Get a holding by ID or raise 404 if not found."""
    holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.portfolio_id == portfolio_id
    ).first()
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    
    return holding


@router.post("/", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def create_holding(
    portfolio_id: str,
    holding_data: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new holding to a portfolio.
    Maximum 100 holdings per portfolio.
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    
    # Check holding count limit
    holding_count = db.query(func.count(Holding.id)).filter(
        Holding.portfolio_id == portfolio_id
    ).scalar()
    
    if holding_count >= MAX_HOLDINGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Portfolio cannot exceed {MAX_HOLDINGS} holdings"
        )
    
    # Check if ticker already exists in this portfolio
    existing = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.ticker == holding_data.ticker
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker {holding_data.ticker} already exists in this portfolio"
        )
    
    # Validate ticker exists in market
    if not MarketDataService.validate_ticker(holding_data.ticker):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker {holding_data.ticker} not found in market data"
        )
    
    # Create new holding
    new_holding = Holding(
        portfolio_id=portfolio_id,
        ticker=holding_data.ticker,
        quantity=holding_data.quantity,
        average_cost=holding_data.average_cost
    )
    
    db.add(new_holding)
    db.commit()
    db.refresh(new_holding)
    
    # Invalidate cached analytics (holdings changed)
    from models.analytics import PortfolioAnalytics
    db.query(PortfolioAnalytics).filter(
        PortfolioAnalytics.portfolio_id == portfolio_id
    ).delete()
    db.commit()
    
    return new_holding


@router.get("/", response_model=List[HoldingResponse])
async def list_holdings(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all holdings for a portfolio.
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    
    holdings = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id
    ).all()
    
    return holdings


@router.get("/{holding_id}", response_model=HoldingResponse)
async def get_holding(
    portfolio_id: str,
    holding_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single holding by ID.
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    return _get_holding_or_404(holding_id, portfolio_id, db)


@router.put("/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    portfolio_id: str,
    holding_id: str,
    holding_data: HoldingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a holding's quantity or average cost.
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    holding = _get_holding_or_404(holding_id, portfolio_id, db)
    
    # Update only provided fields
    if holding_data.quantity is not None:
        holding.quantity = holding_data.quantity
    if holding_data.average_cost is not None:
        holding.average_cost = holding_data.average_cost
    
    db.commit()
    db.refresh(holding)
    
    # Invalidate cached analytics (holdings changed)
    from models.analytics import PortfolioAnalytics
    db.query(PortfolioAnalytics).filter(
        PortfolioAnalytics.portfolio_id == portfolio_id
    ).delete()
    db.commit()
    
    return holding


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    portfolio_id: str,
    holding_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a holding from a portfolio.
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    holding = _get_holding_or_404(holding_id, portfolio_id, db)
    
    db.delete(holding)
    
    # Invalidate cached analytics (holdings changed)
    from models.analytics import PortfolioAnalytics
    db.query(PortfolioAnalytics).filter(
        PortfolioAnalytics.portfolio_id == portfolio_id
    ).delete()
    
    db.commit()
    
    return None
