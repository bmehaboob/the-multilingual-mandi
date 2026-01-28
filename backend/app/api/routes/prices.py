"""
Price API Routes

Provides endpoints for price queries and comparisons.
Requirements: 6.3, 7.5
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.services.price_oracle.price_data_aggregator import PriceDataAggregator
from app.services.price_oracle.price_comparison_engine import PriceComparisonEngine
from app.services.price_oracle.models import Location, PriceAggregation


router = APIRouter(prefix="/prices", tags=["prices"])


class PriceQueryRequest(BaseModel):
    """Request model for price query"""
    commodity: str
    state: Optional[str] = None
    district: Optional[str] = None


class PriceComparisonRequest(BaseModel):
    """Request model for price comparison"""
    commodity: str
    quoted_price: float
    state: Optional[str] = None
    district: Optional[str] = None


# Initialize services
price_aggregator = PriceDataAggregator()
price_comparison_engine = PriceComparisonEngine()


@router.post("/query", response_model=PriceAggregation)
async def query_price(request: PriceQueryRequest):
    """
    Query current market prices for a commodity
    
    Requirement 6.3: Returns price data within 3 seconds
    
    Args:
        request: Price query request with commodity and location
        
    Returns:
        PriceAggregation with min, max, average prices and data sources
    """
    try:
        location = Location(
            state=request.state or "Maharashtra",
            district=request.district
        )
        
        # Aggregate prices from all available sources
        price_data = await price_aggregator.aggregate_prices(
            commodity=request.commodity,
            location=location
        )
        
        return price_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query prices: {str(e)}"
        )


@router.post("/compare")
async def compare_price(request: PriceComparisonRequest):
    """
    Compare a quoted price against market average
    
    Requirement 7.5: Provides price comparison with voice output support
    
    Args:
        request: Price comparison request with commodity, quoted price, and location
        
    Returns:
        PriceAnalysis with verdict (fair/high/low) and comparison message
    """
    try:
        location = Location(
            state=request.state or "Maharashtra",
            district=request.district
        )
        
        # Get market data
        market_data = await price_aggregator.aggregate_prices(
            commodity=request.commodity,
            location=location
        )
        
        # Perform comparison
        analysis = price_comparison_engine.analyze_quote(
            commodity=request.commodity,
            quoted_price=request.quoted_price,
            market_data=market_data
        )
        
        return {
            "verdict": analysis.verdict,
            "message": analysis.message,
            "percentage_difference": analysis.percentage_difference,
            "market_average": analysis.market_average,
            "quoted_price": analysis.quoted_price,
            "market_data": market_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare prices: {str(e)}"
        )


@router.get("/commodities")
async def list_commodities():
    """
    List available commodities
    
    Returns:
        List of commodity names available in the system
    """
    # Get commodities from demo data provider
    from app.services.price_oracle.demo_data_provider import DemoDataProvider
    
    demo_provider = DemoDataProvider()
    commodities = list(demo_provider.demo_data.keys())
    
    return {
        "commodities": sorted(commodities),
        "count": len(commodities)
    }
