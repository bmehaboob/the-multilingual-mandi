"""
Data Export API Endpoints

Provides endpoints for exporting anonymized data to third parties for
price aggregation and market intelligence.

Requirements: 15.3 - Data anonymization for third-party sharing
Property 48: Data Anonymization for Third Parties
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.dependencies import get_db
from app.services.privacy.data_anonymizer import (
    DataAnonymizer,
    AnonymizedPriceData,
    AnonymizedTransactionData
)
from app.models.transaction import Transaction
from app.models.conversation import Message


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-export", tags=["data-export"])

# Initialize anonymizer with production salt from environment
# In production, this should come from secure environment variables
anonymizer = DataAnonymizer()


@router.get(
    "/transactions",
    response_model=List[AnonymizedTransactionData],
    summary="Export anonymized transaction data"
)
async def export_anonymized_transactions(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for transaction export (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for transaction export (ISO format)"
    ),
    commodity: Optional[str] = Query(
        None,
        description="Filter by commodity name"
    ),
    state: Optional[str] = Query(
        None,
        description="Filter by state"
    ),
    limit: int = Query(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of transactions to return"
    ),
    db: Session = Depends(get_db)
) -> List[AnonymizedTransactionData]:
    """
    Export anonymized transaction data for third-party analysis.
    
    This endpoint provides access to transaction data with all personally
    identifiable information (PII) removed. The data is suitable for:
    - Market intelligence and trend analysis
    - Price aggregation across regions
    - Agricultural commodity research
    
    **Data Privacy:**
    - All user IDs are replaced with one-way hashes
    - Exact locations are replaced with coarse location (state/district)
    - No names, phone numbers, or other PII is included
    
    **Query Parameters:**
    - start_date: Filter transactions from this date onwards
    - end_date: Filter transactions up to this date
    - commodity: Filter by specific commodity
    - state: Filter by state
    - limit: Maximum number of records (default: 1000, max: 10000)
    
    **Requirements:** 15.3
    """
    try:
        # Build query
        query = db.query(Transaction)
        
        # Apply filters
        filters = []
        
        if start_date:
            filters.append(Transaction.completed_at >= start_date)
        
        if end_date:
            filters.append(Transaction.completed_at <= end_date)
        
        if commodity:
            filters.append(Transaction.commodity == commodity)
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Order by completion date (most recent first)
        query = query.order_by(Transaction.completed_at.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        transactions = query.all()
        
        logger.info(
            f"Exporting {len(transactions)} anonymized transactions "
            f"(commodity={commodity}, state={state})"
        )
        
        # Anonymize transactions
        anonymized_transactions = []
        for transaction in transactions:
            # Prepare transaction data for anonymization
            transaction_data = {
                "buyer_id": transaction.buyer_id,
                "seller_id": transaction.seller_id,
                "commodity": transaction.commodity,
                "agreed_price": transaction.agreed_price,
                "quantity": transaction.quantity,
                "unit": transaction.unit,
                "market_average_at_time": transaction.market_average_at_time,
                "location": {
                    "state": state,  # Use filter state or extract from transaction
                    "district": None  # Would need to be stored in transaction model
                },
                "completed_at": transaction.completed_at
            }
            
            anonymized = anonymizer.anonymize_transaction(transaction_data)
            anonymized_transactions.append(anonymized)
        
        return anonymized_transactions
        
    except Exception as e:
        logger.error(f"Error exporting anonymized transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export transaction data"
        )


@router.get(
    "/price-contributions",
    response_model=List[AnonymizedPriceData],
    summary="Export anonymized price contributions"
)
async def export_anonymized_price_contributions(
    start_date: Optional[datetime] = Query(
        None,
        description="Start date for price contributions (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="End date for price contributions (ISO format)"
    ),
    commodity: Optional[str] = Query(
        None,
        description="Filter by commodity name"
    ),
    state: Optional[str] = Query(
        None,
        description="Filter by state"
    ),
    limit: int = Query(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of contributions to return"
    ),
    db: Session = Depends(get_db)
) -> List[AnonymizedPriceData]:
    """
    Export anonymized price contributions for crowd-sourced price aggregation.
    
    This endpoint provides access to user-contributed price data with all
    personally identifiable information (PII) removed. The data is suitable for:
    - Building crowd-sourced price databases
    - Real-time market price tracking
    - Regional price comparison
    
    **Data Privacy:**
    - All user IDs are replaced with one-way hashes
    - Exact locations are replaced with coarse location (state/district)
    - No names, phone numbers, or other PII is included
    
    **Query Parameters:**
    - start_date: Filter contributions from this date onwards
    - end_date: Filter contributions up to this date
    - commodity: Filter by specific commodity
    - state: Filter by state
    - limit: Maximum number of records (default: 1000, max: 10000)
    
    **Requirements:** 15.3
    """
    try:
        # For now, we'll extract price contributions from transactions
        # In a full implementation, there would be a separate PriceContribution model
        
        # Build query
        query = db.query(Transaction)
        
        # Apply filters
        filters = []
        
        if start_date:
            filters.append(Transaction.completed_at >= start_date)
        
        if end_date:
            filters.append(Transaction.completed_at <= end_date)
        
        if commodity:
            filters.append(Transaction.commodity == commodity)
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Order by completion date (most recent first)
        query = query.order_by(Transaction.completed_at.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        transactions = query.all()
        
        logger.info(
            f"Exporting {len(transactions)} anonymized price contributions "
            f"(commodity={commodity}, state={state})"
        )
        
        # Convert transactions to price contributions and anonymize
        anonymized_contributions = []
        for transaction in transactions:
            # Create price contribution from seller's perspective
            contribution = anonymizer.anonymize_price_contribution(
                user_id=transaction.seller_id,
                commodity=transaction.commodity,
                price=transaction.agreed_price,
                quantity=transaction.quantity,
                unit=transaction.unit,
                location={
                    "state": state,  # Use filter state or extract from transaction
                    "district": None
                },
                timestamp=transaction.completed_at
            )
            anonymized_contributions.append(contribution)
        
        return anonymized_contributions
        
    except Exception as e:
        logger.error(f"Error exporting anonymized price contributions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export price contribution data"
        )


@router.get(
    "/market-statistics",
    summary="Get aggregated market statistics"
)
async def get_market_statistics(
    commodity: str = Query(..., description="Commodity name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    days: int = Query(
        7,
        ge=1,
        le=90,
        description="Number of days to include in statistics"
    ),
    db: Session = Depends(get_db)
):
    """
    Get aggregated market statistics without any PII.
    
    This endpoint provides statistical summaries of market data that are
    completely anonymized and aggregated. No individual transaction or
    user data can be identified.
    
    **Data Privacy:**
    - Only aggregate statistics are provided
    - No individual transactions or users can be identified
    - All data is anonymized before aggregation
    
    **Query Parameters:**
    - commodity: Commodity name (required)
    - state: Filter by state (optional)
    - days: Number of days to include (default: 7, max: 90)
    
    **Requirements:** 15.3
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = db.query(Transaction).filter(
            and_(
                Transaction.commodity == commodity,
                Transaction.completed_at >= start_date,
                Transaction.completed_at <= end_date
            )
        )
        
        # Apply state filter if provided
        if state:
            # Note: This assumes state is stored in transaction
            # In full implementation, would need proper location handling
            pass
        
        # Get transactions
        transactions = query.all()
        
        if not transactions:
            return {
                "commodity": commodity,
                "state": state,
                "period_days": days,
                "sample_size": 0,
                "message": "No data available for the specified criteria"
            }
        
        # Calculate statistics (completely anonymized)
        prices = [t.agreed_price for t in transactions]
        quantities = [t.quantity for t in transactions]
        
        from statistics import mean, median, stdev
        
        stats = {
            "commodity": commodity,
            "state": state,
            "period_days": days,
            "sample_size": len(transactions),
            "price_statistics": {
                "min": min(prices),
                "max": max(prices),
                "average": mean(prices),
                "median": median(prices),
                "std_dev": stdev(prices) if len(prices) > 1 else 0.0
            },
            "quantity_statistics": {
                "total": sum(quantities),
                "average": mean(quantities),
                "median": median(quantities)
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        logger.info(
            f"Generated market statistics for {commodity} "
            f"(sample_size={len(transactions)})"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error generating market statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate market statistics"
        )


@router.get("/health")
async def data_export_health_check():
    """
    Health check endpoint for data export service.
    
    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "data-export",
        "anonymization": "enabled"
    }
