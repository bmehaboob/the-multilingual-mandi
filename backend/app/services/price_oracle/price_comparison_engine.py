"""Price comparison engine for analyzing quoted prices against market data"""
from typing import Optional
from pydantic import BaseModel

from .models import PriceAggregation


class PriceAnalysis(BaseModel):
    """Result of price comparison analysis"""
    verdict: str  # "fair", "high", or "low"
    message: str
    percentage_difference: float
    market_average: float
    quoted_price: float


class PriceComparisonEngine:
    """
    Compares quoted prices against market data and provides analysis.
    
    Classification rules:
    - Fair: Within 5% of market average
    - High: More than 10% above market average
    - Low: More than 10% below market average
    """
    
    def __init__(self):
        self.fair_threshold = 0.05  # 5%
        self.high_threshold = 0.10  # 10%
        self.low_threshold = 0.10   # 10%
    
    def analyze_quote(
        self,
        commodity: str,
        quoted_price: float,
        market_data: PriceAggregation
    ) -> PriceAnalysis:
        """
        Analyzes if quote is fair, high, or low compared to market average
        
        Args:
            commodity: Name of the commodity
            quoted_price: Price quoted by seller
            market_data: Aggregated market price data
            
        Returns:
            PriceAnalysis with verdict and user-friendly message
        """
        avg = market_data.average_price
        
        # Calculate percentage difference
        percentage_diff = ((quoted_price - avg) / avg) * 100
        
        # Classify the price
        if abs(quoted_price - avg) <= self.fair_threshold * avg:
            # Within 5% - Fair price
            verdict = "fair"
            message = (
                f"Price is fair. The quoted price of ₹{quoted_price:.2f} is close to "
                f"the market average of ₹{avg:.2f} per {market_data.location.state or 'your area'}."
            )
        elif quoted_price > avg + self.high_threshold * avg:
            # More than 10% above - High price
            verdict = "high"
            message = (
                f"Price is high. The quoted price of ₹{quoted_price:.2f} is "
                f"{abs(percentage_diff):.1f}% above the market average of ₹{avg:.2f}. "
                f"You may want to negotiate."
            )
        elif quoted_price < avg - self.low_threshold * avg:
            # More than 10% below - Low price
            verdict = "low"
            message = (
                f"Price is unusually low. The quoted price of ₹{quoted_price:.2f} is "
                f"{abs(percentage_diff):.1f}% below the market average of ₹{avg:.2f}. "
                f"This is a good deal, but verify the quality."
            )
        else:
            # Between 5% and 10% - Slightly high or low
            if quoted_price > avg:
                verdict = "slightly_high"
                message = (
                    f"Price is slightly high. The quoted price of ₹{quoted_price:.2f} is "
                    f"{abs(percentage_diff):.1f}% above the market average of ₹{avg:.2f}."
                )
            else:
                verdict = "slightly_low"
                message = (
                    f"Price is slightly low. The quoted price of ₹{quoted_price:.2f} is "
                    f"{abs(percentage_diff):.1f}% below the market average of ₹{avg:.2f}."
                )
        
        return PriceAnalysis(
            verdict=verdict,
            message=message,
            percentage_difference=percentage_diff,
            market_average=avg,
            quoted_price=quoted_price
        )
    
    def get_price_range_message(
        self,
        market_data: PriceAggregation
    ) -> str:
        """
        Generates a message about the price range in the market
        
        Args:
            market_data: Aggregated market price data
            
        Returns:
            User-friendly message about price range
        """
        return (
            f"Current market prices for {market_data.commodity} range from "
            f"₹{market_data.min_price:.2f} to ₹{market_data.max_price:.2f} per kg, "
            f"with an average of ₹{market_data.average_price:.2f}. "
            f"Based on {market_data.sample_size} price points."
        )
    
    def compare_with_range(
        self,
        quoted_price: float,
        market_data: PriceAggregation
    ) -> str:
        """
        Compares quoted price with the full market range
        
        Args:
            quoted_price: Price quoted by seller
            market_data: Aggregated market price data
            
        Returns:
            Message indicating where the quote falls in the range
        """
        if quoted_price < market_data.min_price:
            return f"This price is below the lowest market price of ₹{market_data.min_price:.2f}."
        elif quoted_price > market_data.max_price:
            return f"This price is above the highest market price of ₹{market_data.max_price:.2f}."
        else:
            return f"This price falls within the current market range."
