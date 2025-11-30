"""
Market data service using yfinance for stock price data.
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd


class MarketDataService:
    """Service for fetching market data from Yahoo Finance."""
    
    @staticmethod
    def validate_ticker(ticker: str) -> bool:
        """
        Validate if a ticker symbol exists.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            True if ticker is valid, False otherwise
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # Check if we got actual data back
            return 'regularMarketPrice' in info or 'currentPrice' in info
        except Exception:
            return False
    
    @staticmethod
    def get_current_price(ticker: str) -> Optional[float]:
        """
        Get current price for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current price or None if not found
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('regularMarketPrice') or info.get('currentPrice')
        except Exception:
            return None
    
    @staticmethod
    def get_historical_prices(
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Get historical price data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Period string ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            DataFrame with historical prices (Date, Open, High, Low, Close, Volume)
        """
        try:
            stock = yf.Ticker(ticker)
            
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)
            
            return df
        except Exception as e:
            raise ValueError(f"Failed to fetch historical data for {ticker}: {str(e)}")
    
    @staticmethod
    def get_multiple_prices(tickers: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple tickers efficiently.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to current price
        """
        prices = {}
        
        try:
            # Download all tickers at once for efficiency
            data = yf.download(
                tickers,
                period="1d",
                progress=False,
                threads=True
            )
            
            if len(tickers) == 1:
                # Single ticker returns different structure
                prices[tickers[0]] = data['Close'].iloc[-1] if not data.empty else None
            else:
                # Multiple tickers
                for ticker in tickers:
                    try:
                        prices[ticker] = data['Close'][ticker].iloc[-1]
                    except Exception:
                        prices[ticker] = None
        except Exception:
            # Fallback to individual requests
            for ticker in tickers:
                prices[ticker] = MarketDataService.get_current_price(ticker)
        
        return prices
    
    @staticmethod
    def get_ticker_info(ticker: str) -> Dict:
        """
        Get detailed information about a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with ticker information (name, sector, industry, etc.)
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'symbol': ticker,
                'name': info.get('longName', ticker),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange'),
                'market_cap': info.get('marketCap'),
                'current_price': info.get('regularMarketPrice') or info.get('currentPrice')
            }
        except Exception as e:
            raise ValueError(f"Failed to fetch info for {ticker}: {str(e)}")
