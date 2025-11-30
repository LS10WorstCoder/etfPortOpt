"""
Market data API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime

from services.market_data import MarketDataService
from models.user import User
from api.auth import get_current_user

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/validate/{ticker}")
async def validate_ticker(
    ticker: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate if a ticker symbol exists.
    """
    ticker = ticker.upper().strip()
    is_valid = MarketDataService.validate_ticker(ticker)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{ticker}' not found"
        )
    
    return {
        "ticker": ticker,
        "valid": True
    }


@router.get("/price/{ticker}")
async def get_price(
    ticker: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get current price for a ticker.
    """
    ticker = ticker.upper().strip()
    price = MarketDataService.get_current_price(ticker)
    
    if price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price data not available for '{ticker}'"
        )
    
    return {
        "ticker": ticker,
        "price": price,
        "currency": "USD"
    }


@router.get("/info/{ticker}")
async def get_ticker_info(
    ticker: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a ticker.
    """
    ticker = ticker.upper().strip()
    
    try:
        info = MarketDataService.get_ticker_info(ticker)
        return info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/historical/{ticker}")
async def get_historical_data(
    ticker: str,
    period: str = "1y",
    current_user: User = Depends(get_current_user)
):
    """
    Get historical price data for a ticker.
    
    Supported periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    ticker = ticker.upper().strip()
    
    valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    try:
        df = MarketDataService.get_historical_prices(ticker, period=period)
        
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data available for '{ticker}'"
            )
        
        # Convert DataFrame to JSON-friendly format
        df_reset = df.reset_index()
        df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
        
        return {
            "ticker": ticker,
            "period": period,
            "data": df_reset.to_dict(orient='records')
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
