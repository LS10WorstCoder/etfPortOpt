"""
CSV Import/Export endpoints for portfolio holdings.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io
from decimal import Decimal, InvalidOperation

from database import get_db
from api.auth import get_current_user
from models.user import User
from models.holding import Holding
from models.analytics import PortfolioAnalytics
from schemas.csv import HoldingCSVRow, CSVImportResponse
from services.market_data import MarketDataService
from utils.portfolio_utils import get_user_portfolio_or_404

router = APIRouter(tags=["csv"])

MAX_HOLDINGS = 100  # Same limit as holdings API


@router.post("/portfolios/{portfolio_id}/import", response_model=CSVImportResponse)
async def import_holdings_csv(
    portfolio_id: str,
    file: UploadFile = File(...),
    overwrite: bool = Query(default=False),
    validate_tickers: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import portfolio holdings from CSV file.
    
    CSV Format (with header):
    ```
    ticker,quantity,average_cost
    AAPL,10,150.50
    MSFT,25,300.00
    GOOGL,5,120.75
    ```
    
    Rules:
    - First row must be header: ticker,quantity,average_cost
    - ticker: Required, 1-10 characters
    - quantity: Required, positive decimal
    - average_cost: Optional, non-negative decimal
    - Max 100 holdings per portfolio
    - Duplicate tickers in CSV will be merged (last value wins)
    
    Args:
        portfolio_id: Portfolio to import into
        file: CSV file upload
        overwrite: If true, delete existing holdings before import (default: false)
        validate_tickers: If true, validate tickers exist in market (default: true)
        
    Returns:
        Import summary with success count and errors
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    
    # Check file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Read CSV content
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")
    
    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(text_content))
    
    # Validate header
    expected_fields = {'ticker', 'quantity', 'average_cost'}
    if not expected_fields.issubset(set(csv_reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have headers: {', '.join(expected_fields)}"
        )
    
    # Parse and validate rows
    rows_to_import = {}
    errors = []
    row_num = 1
    
    for row in csv_reader:
        row_num += 1
        ticker = row.get('ticker', '').strip().upper()
        
        if not ticker:
            errors.append(f"Row {row_num}: Missing ticker")
            continue
        
        try:
            # Parse quantity
            quantity_str = row.get('quantity', '').strip()
            if not quantity_str:
                errors.append(f"Row {row_num} ({ticker}): Missing quantity")
                continue
            quantity = Decimal(quantity_str)
            
            if quantity <= 0:
                errors.append(f"Row {row_num} ({ticker}): Quantity must be positive")
                continue
            
            # Parse average_cost (optional)
            avg_cost_str = row.get('average_cost', '').strip()
            average_cost = Decimal(avg_cost_str) if avg_cost_str else None
            
            if average_cost is not None and average_cost < 0:
                errors.append(f"Row {row_num} ({ticker}): Average cost cannot be negative")
                continue
            
            # Validate ticker length
            if len(ticker) > 10:
                errors.append(f"Row {row_num} ({ticker}): Ticker too long (max 10 chars)")
                continue
            
            # Store (last occurrence wins for duplicates)
            rows_to_import[ticker] = {
                'ticker': ticker,
                'quantity': quantity,
                'average_cost': average_cost
            }
            
        except (InvalidOperation, ValueError) as e:
            errors.append(f"Row {row_num} ({ticker}): Invalid number format")
            continue
    
    total_rows = row_num - 1
    
    if not rows_to_import:
        return CSVImportResponse(
            success=False,
            total_rows=total_rows,
            imported=0,
            skipped=total_rows,
            errors=errors + ["No valid holdings to import"],
            holdings=[]
        )
    
    # Validate tickers exist in market (if enabled)
    if validate_tickers:
        for ticker in rows_to_import.keys():
            if not MarketDataService.validate_ticker(ticker):
                errors.append(f"Ticker {ticker}: Not found in market data")
                del rows_to_import[ticker]
    
    # Check holdings limit
    existing_count = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id
    ).count()
    
    if overwrite:
        available_slots = MAX_HOLDINGS
    else:
        available_slots = MAX_HOLDINGS - existing_count
    
    if len(rows_to_import) > available_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot import {len(rows_to_import)} holdings. "
                   f"Portfolio limit: {MAX_HOLDINGS}, Current: {existing_count}, "
                   f"Available: {available_slots}"
        )
    
    # Delete existing holdings if overwrite mode
    if overwrite:
        db.query(Holding).filter(Holding.portfolio_id == portfolio_id).delete()
        db.commit()
    
    # Import holdings
    imported_holdings = []
    skipped = 0
    
    for ticker, data in rows_to_import.items():
        # Check if ticker already exists (unless overwrite)
        if not overwrite:
            existing = db.query(Holding).filter(
                Holding.portfolio_id == portfolio_id,
                Holding.ticker == ticker
            ).first()
            
            if existing:
                errors.append(f"Ticker {ticker}: Already exists (skipped)")
                skipped += 1
                continue
        
        # Create holding
        new_holding = Holding(
            portfolio_id=portfolio_id,
            ticker=data['ticker'],
            quantity=data['quantity'],
            average_cost=data['average_cost']
        )
        db.add(new_holding)
        imported_holdings.append({
            'ticker': data['ticker'],
            'quantity': float(data['quantity']),
            'average_cost': float(data['average_cost']) if data['average_cost'] else None
        })
    
    db.commit()
    
    # Invalidate cached analytics
    db.query(PortfolioAnalytics).filter(
        PortfolioAnalytics.portfolio_id == portfolio_id
    ).delete()
    db.commit()
    
    return CSVImportResponse(
        success=True,
        total_rows=total_rows,
        imported=len(imported_holdings),
        skipped=skipped + (total_rows - len(rows_to_import) - len(errors)),
        errors=errors,
        holdings=imported_holdings
    )


@router.get("/portfolios/{portfolio_id}/export")
async def export_holdings_csv(
    portfolio_id: str,
    include_header: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export portfolio holdings to CSV file.
    
    Returns CSV with columns: ticker, quantity, average_cost
    
    Args:
        portfolio_id: Portfolio to export
        include_header: Whether to include header row (default: true)
        
    Returns:
        CSV file download
    """
    portfolio = get_user_portfolio_or_404(portfolio_id, current_user, db)
    
    # Get holdings
    holdings = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id
    ).all()
    
    if not holdings:
        raise HTTPException(
            status_code=404,
            detail="No holdings found in portfolio"
        )
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    if include_header:
        writer.writerow(['ticker', 'quantity', 'average_cost'])
    
    # Write data
    for holding in holdings:
        writer.writerow([
            holding.ticker,
            str(holding.quantity),
            str(holding.average_cost) if holding.average_cost else ''
        ])
    
    # Prepare response
    output.seek(0)
    filename = f"portfolio_{portfolio.name.replace(' ', '_')}_{portfolio_id}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
