"""
Optimization endpoint for portfolio optimization.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict
from pydantic import BaseModel, Field

from database import get_db
from api.auth import get_current_user
from models.user import User
from models.optimization import OptimizationResult
from services.portfolio_optimizer import PortfolioOptimizer
from services.portfolio_analyzer import PortfolioAnalyzer
from utils.portfolio_utils import get_user_portfolio_or_404, get_portfolio_holdings_or_error

router = APIRouter(tags=["optimization"])


class WeightConstraint(BaseModel):
    """Weight constraint for a single ticker."""
    min: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum allocation (0-1)")
    max: float = Field(default=1.0, ge=0.0, le=1.0, description="Maximum allocation (0-1)")


class OptimizationRequest(BaseModel):
    """Request body for portfolio optimization."""
    constraints: Optional[Dict[str, WeightConstraint]] = Field(
        default=None,
        description="Per-ticker weight constraints",
        example={"AAPL": {"min": 0.2, "max": 0.4}, "MSFT": {"min": 0.3, "max": 0.6}}
    )


@router.post("/portfolios/{portfolio_id}/optimize")
async def optimize_portfolio(
    portfolio_id: str,
    strategy: str = Query(..., regex="^(max_sharpe|min_volatility|equal_weight)$"),
    period: str = Query(default="1y", regex="^(1y|2y|5y|10y)$"),
    save_results: bool = Query(default=True),
    request_body: OptimizationRequest = Body(default=OptimizationRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimize portfolio allocation using Modern Portfolio Theory.
    
    **Strategies:**
    - `max_sharpe`: Maximize risk-adjusted return (Sharpe ratio)
    - `min_volatility`: Minimize portfolio risk (standard deviation)
    - `equal_weight`: Baseline strategy with equal allocation (1/N)
    
    **Weight Constraints (Optional):**
    Set min/max allocation limits per ticker:
    ```json
    {
      "constraints": {
        "AAPL": {"min": 0.2, "max": 0.4},
        "MSFT": {"min": 0.3, "max": 0.6}
      }
    }
    ```
    
    **Returns:**
    - Optimized weights for each ticker
    - Expected annual return, volatility, and Sharpe ratio
    - Comparison with current allocation
    
    Args:
        portfolio_id: Portfolio to optimize
        strategy: Optimization strategy
        period: Historical period for analysis (1y, 2y, 5y, 10y)
        save_results: Whether to save results to database
        request_body: Optional weight constraints
        
    Returns:
        Optimization results with recommended allocation
    """
    # Verify portfolio exists and user owns it
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    holdings = get_portfolio_holdings_or_error(portfolio_id, db)
    
    # Extract tickers
    tickers = [h.ticker for h in holdings]
    
    # Convert Pydantic constraints to dict format for optimizer
    constraints_dict = None
    if request_body.constraints:
        constraints_dict = {
            ticker: {'min': c.min, 'max': c.max}
            for ticker, c in request_body.constraints.items()
        }
        
        # Validate that constrained tickers exist in portfolio
        invalid_tickers = set(constraints_dict.keys()) - set(tickers)
        if invalid_tickers:
            raise HTTPException(
                status_code=400,
                detail=f"Constraints specified for tickers not in portfolio: {invalid_tickers}"
            )
    
    try:
        # Run optimization
        optimizer = PortfolioOptimizer(tickers, period=period)
        results = optimizer.optimize(strategy, constraints=constraints_dict)
        
        # Calculate current allocation for comparison
        current_allocation = PortfolioAnalyzer.calculate_weights_from_holdings(holdings)
        results['current_allocation'] = current_allocation
        
        # Calculate rebalancing needed
        if current_allocation:
            rebalancing = {
                ticker: results['weights'][ticker] - current_allocation.get(ticker, 0)
                for ticker in tickers
            }
            results['rebalancing_needed'] = rebalancing
        
        # Save to database if requested
        if save_results:
            optimization_record = OptimizationResult(
                portfolio_id=portfolio_id,
                strategy=strategy,
                optimized_weights=results['weights'],
                expected_return=results['expected_return'],
                expected_volatility=results['expected_volatility'],
                sharpe_ratio=results['sharpe_ratio']
            )
            db.add(optimization_record)
            db.commit()
            db.refresh(optimization_record)
            
            results['saved_to_db'] = True
            results['optimization_id'] = str(optimization_record.id)
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}/optimizations/history")
async def get_optimization_history(
    portfolio_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    strategy: Optional[str] = Query(default=None, regex="^(max_sharpe|min_volatility|equal_weight)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get historical optimization results for a portfolio.
    
    Returns saved optimization records ordered by creation date (newest first).
    Optionally filter by strategy.
    
    Args:
        portfolio_id: Portfolio ID
        limit: Maximum number of records to return
        strategy: Optional strategy filter
        
    Returns:
        List of historical optimization records
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    
    query = db.query(OptimizationResult).filter(
        OptimizationResult.portfolio_id == portfolio_id
    )
    
    # Apply strategy filter if provided
    if strategy:
        query = query.filter(OptimizationResult.strategy == strategy)
    
    # Get results
    optimizations = query.order_by(
        OptimizationResult.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            'id': str(o.id),
            'portfolio_id': str(o.portfolio_id),
            'strategy': o.strategy,
            'optimized_weights': o.optimized_weights,
            'expected_return': float(o.expected_return) if o.expected_return else None,
            'expected_volatility': float(o.expected_volatility) if o.expected_volatility else None,
            'sharpe_ratio': float(o.sharpe_ratio) if o.sharpe_ratio else None,
            'created_at': o.created_at
        }
        for o in optimizations
    ]
