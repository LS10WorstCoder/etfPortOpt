"""
Analytics endpoint for portfolio analysis.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from api.auth import get_current_user
from models.user import User
from models.analytics import PortfolioAnalytics
from services.portfolio_analyzer import PortfolioAnalyzer
from utils.portfolio_utils import get_user_portfolio_or_404, get_portfolio_holdings_or_error

router = APIRouter(tags=["analytics"])


@router.post("/portfolios/{portfolio_id}/analyze")
async def analyze_portfolio(
    portfolio_id: str,
    period: str = Query(default="1y", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    save_results: bool = Query(default=True),
    use_cache: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze portfolio risk and performance metrics.
    
    Calculates:
    - Total portfolio value
    - Annual return
    - Volatility (annualized standard deviation)
    - Sharpe ratio (risk-adjusted return)
    - Maximum drawdown (largest peak-to-trough decline)
    - Value at Risk 95% (daily loss not exceeded 95% of the time)
    - Correlation matrix between holdings
    
    Caching:
    - Returns cached results if < 1 hour old and holdings unchanged
    - Set use_cache=false to force fresh calculation
    - Cache invalidated when holdings are added/updated/deleted
    
    Args:
        portfolio_id: Portfolio to analyze
        period: Historical period (1y, 2y, 5y, etc.)
        save_results: Whether to save results to database
        use_cache: Whether to use cached results (default: true)
        
    Returns:
        Complete portfolio analysis with risk metrics
    """
    from datetime import datetime, timedelta
    
    # Verify portfolio exists and user owns it
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    holdings = get_portfolio_holdings_or_error(portfolio_id, db)
    
    # Check for cached results if caching enabled
    if use_cache:
        # Get most recent analytics record
        latest_analytics = db.query(PortfolioAnalytics).filter(
            PortfolioAnalytics.portfolio_id == portfolio_id
        ).order_by(PortfolioAnalytics.created_at.desc()).first()
        
        if latest_analytics:
            # Check if cache is fresh (< 1 hour old)
            from datetime import timezone
            now = datetime.now(timezone.utc)
            cache_age = now - latest_analytics.created_at.replace(tzinfo=timezone.utc)
            is_fresh = cache_age < timedelta(hours=1)
            
            # Check if holdings changed since last analysis
            holdings_last_modified = max(
                (h.created_at.replace(tzinfo=timezone.utc) for h in holdings),
                default=portfolio.updated_at.replace(tzinfo=timezone.utc)
            )
            cache_is_newer = latest_analytics.created_at.replace(tzinfo=timezone.utc) > holdings_last_modified
            
            if is_fresh and cache_is_newer:
                # Return cached results
                return {
                    'total_value': float(latest_analytics.total_value),
                    'annual_return': float(latest_analytics.daily_return) * 252,
                    'volatility': float(latest_analytics.volatility),
                    'sharpe_ratio': float(latest_analytics.sharpe_ratio),
                    'period': period,
                    'calculated_at': latest_analytics.created_at.isoformat(),
                    'cached': True,
                    'cache_age_seconds': int(cache_age.total_seconds())
                }
    
    # Convert holdings to dict format for analyzer
    holdings_data = [
        {
            'ticker': h.ticker,
            'quantity': h.quantity,
            'average_cost': h.average_cost
        }
        for h in holdings
    ]
    
    try:
        # Perform analysis
        analyzer = PortfolioAnalyzer(holdings_data, period=period)
        results = analyzer.analyze()
        
        # Save to database if requested
        if save_results:
            analytics_record = PortfolioAnalytics(
                portfolio_id=portfolio_id,
                calculation_date=results['calculated_at'],
                total_value=results['total_value'],
                daily_return=results['annual_return'] / 252,  # Convert to daily
                volatility=results['volatility'],
                sharpe_ratio=results['sharpe_ratio']
            )
            db.add(analytics_record)
            db.commit()
            db.refresh(analytics_record)
            
            results['saved_to_db'] = True
            results['analytics_id'] = analytics_record.id
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}/analytics/history")
async def get_analytics_history(
    portfolio_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get historical analytics for a portfolio.
    
    Returns saved analytics records ordered by calculation date (newest first).
    
    Args:
        portfolio_id: Portfolio ID
        limit: Maximum number of records to return
        
    Returns:
        List of historical analytics records
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    
    analytics = db.query(PortfolioAnalytics).filter(
        PortfolioAnalytics.portfolio_id == portfolio_id
    ).order_by(
        PortfolioAnalytics.calculation_date.desc()
    ).limit(limit).all()
    
    return [
        {
            'id': a.id,
            'portfolio_id': a.portfolio_id,
            'calculation_date': a.calculation_date,
            'total_value': a.total_value,
            'daily_return': a.daily_return,
            'volatility': a.volatility,
            'sharpe_ratio': a.sharpe_ratio,
            'created_at': a.created_at
        }
        for a in analytics
    ]
