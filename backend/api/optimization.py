"""
Optimization endpoint for portfolio optimization.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict
from pydantic import BaseModel, Field
import numpy as np

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
    strategy: str = Query(..., pattern="^(max_sharpe|min_volatility|equal_weight|equal_risk)$"),
    period: str = Query(default="1y", pattern="^(1y|2y|5y|10y)$"),
    target_duration: str = Query(default="1y", pattern="^(6m|1y|2y|3y|4y|5y|10y)$"),
    max_drawdown: Optional[float] = Query(default=None, ge=0.05, le=0.50),
    run_monte_carlo: bool = Query(default=False),
    confidence_level: int = Query(default=95, ge=80, le=95),
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
    - `equal_risk`: Risk parity - each asset contributes equally to portfolio risk
    
    **Investment Horizon:**
    - `target_duration`: How long you plan to hold (6m, 1y, 2y, 3y, 4y, 5y, 10y)
    - Shorter durations (6m) prioritize stability over long-term growth
    - Returns and volatility are scaled to match your timeframe
    
    **Risk Controls:**
    - `max_drawdown`: Maximum acceptable loss (0.10 = 10%, 0.15 = 15%, etc.)
    - Optimizer will respect this historical drawdown limit
    
    **Monte Carlo Simulation:**
    - `run_monte_carlo`: Generate probability distribution of outcomes
    - `confidence_level`: 80%, 90%, or 95% confidence interval
    - Shows range of possible returns and probability of loss
    
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
    - Expected return, volatility, and Sharpe ratio (scaled to target_duration)
    - Comparison with current allocation
    - Optional Monte Carlo simulation results
    
    Args:
        portfolio_id: Portfolio to optimize
        strategy: Optimization strategy
        period: Historical period for analysis (1y, 2y, 5y, 10y)
        target_duration: Investment horizon (6m, 1y, 2y, 3y, 4y, 5y, 10y)
        max_drawdown: Maximum drawdown constraint (0.05 to 0.50)
        run_monte_carlo: Whether to run Monte Carlo simulation
        confidence_level: Confidence level for Monte Carlo (80, 90, 95)
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
        # Check if portfolio requires whole shares (retirement accounts)
        whole_shares = portfolio.account_type in ['roth_ira', 'traditional_ira', '401k']
        
        # Run optimization
        optimizer = PortfolioOptimizer(
            tickers, 
            period=period, 
            whole_shares=whole_shares,
            target_duration=target_duration,
            max_drawdown=max_drawdown
        )
        results = optimizer.optimize(strategy, constraints=constraints_dict)
        
        # Add account type context to results
        results['account_type'] = portfolio.account_type
        if whole_shares:
            results['note'] = 'Weights adjusted for whole-share allocations (retirement account).'
        
        # Run Monte Carlo simulation if requested
        if run_monte_carlo:
            weights_array = np.array([results['weights'][t] for t in tickers])
            mc_results = optimizer.monte_carlo_simulation(
                weights_array, 
                confidence_level=confidence_level
            )
            results['monte_carlo'] = mc_results
        
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
    strategy: Optional[str] = Query(default=None, pattern="^(max_sharpe|min_volatility|equal_weight|equal_risk)$"),
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
