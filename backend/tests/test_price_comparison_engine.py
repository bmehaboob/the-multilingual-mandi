"""Unit tests for PriceComparisonEngine"""
import pytest
from datetime import datetime

from app.services.price_oracle.price_comparison_engine import (
    PriceComparisonEngine,
    PriceAnalysis,
)
from app.services.price_oracle.models import (
    Location,
    PriceAggregation,
    PriceSource,
)


def create_market_data(
    commodity: str = "tomato",
    average_price: float = 100.0,
    min_price: float = 90.0,
    max_price: float = 110.0
) -> PriceAggregation:
    """Helper to create market data for testing"""
    return PriceAggregation(
        commodity=commodity,
        location=Location(state="Maharashtra"),
        min_price=min_price,
        max_price=max_price,
        average_price=average_price,
        median_price=average_price,
        std_dev=5.0,
        sample_size=10,
        sources_used=[PriceSource.DEMO]
    )


def test_analyze_quote_fair_price():
    """Test that prices within 5% of average are classified as fair"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    # Test exactly at average
    result = engine.analyze_quote("tomato", 100.0, market_data)
    assert result.verdict == "fair"
    assert result.market_average == 100.0
    assert result.quoted_price == 100.0
    
    # Test 3% above (within 5%)
    result = engine.analyze_quote("tomato", 103.0, market_data)
    assert result.verdict == "fair"
    
    # Test 5% above (at threshold)
    result = engine.analyze_quote("tomato", 105.0, market_data)
    assert result.verdict == "fair"
    
    # Test 3% below (within 5%)
    result = engine.analyze_quote("tomato", 97.0, market_data)
    assert result.verdict == "fair"


def test_analyze_quote_high_price():
    """Test that prices >10% above average are classified as high"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    # Test 15% above (clearly high)
    result = engine.analyze_quote("tomato", 115.0, market_data)
    assert result.verdict == "high"
    assert "high" in result.message.lower()
    assert "15.0%" in result.message
    assert result.percentage_difference == 15.0
    
    # Test 11% above (just over threshold)
    result = engine.analyze_quote("tomato", 111.0, market_data)
    assert result.verdict == "high"
    
    # Test 20% above
    result = engine.analyze_quote("tomato", 120.0, market_data)
    assert result.verdict == "high"
    assert result.percentage_difference == 20.0


def test_analyze_quote_low_price():
    """Test that prices >10% below average are classified as low"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    # Test 15% below (clearly low)
    result = engine.analyze_quote("tomato", 85.0, market_data)
    assert result.verdict == "low"
    assert "low" in result.message.lower()
    assert "15.0%" in result.message
    assert result.percentage_difference == -15.0
    
    # Test 11% below (just over threshold)
    result = engine.analyze_quote("tomato", 89.0, market_data)
    assert result.verdict == "low"
    
    # Test 20% below
    result = engine.analyze_quote("tomato", 80.0, market_data)
    assert result.verdict == "low"
    assert result.percentage_difference == -20.0


def test_analyze_quote_slightly_high():
    """Test prices between 5% and 10% above average"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    # Test 7% above (between 5% and 10%)
    result = engine.analyze_quote("tomato", 107.0, market_data)
    assert result.verdict == "slightly_high"
    assert "slightly high" in result.message.lower()
    
    # Test 9% above
    result = engine.analyze_quote("tomato", 109.0, market_data)
    assert result.verdict == "slightly_high"


def test_analyze_quote_slightly_low():
    """Test prices between 5% and 10% below average"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    # Test 7% below (between 5% and 10%)
    result = engine.analyze_quote("tomato", 93.0, market_data)
    assert result.verdict == "slightly_low"
    assert "slightly low" in result.message.lower()
    
    # Test 9% below
    result = engine.analyze_quote("tomato", 91.0, market_data)
    assert result.verdict == "slightly_low"


def test_analyze_quote_with_different_commodities():
    """Test analysis works with different commodities"""
    engine = PriceComparisonEngine()
    
    # Test with rice
    rice_data = create_market_data(commodity="rice", average_price=35.0)
    result = engine.analyze_quote("rice", 40.0, rice_data)
    assert result.verdict == "high"
    
    # Test with wheat
    wheat_data = create_market_data(commodity="wheat", average_price=28.0)
    result = engine.analyze_quote("wheat", 28.0, wheat_data)
    assert result.verdict == "fair"


def test_analyze_quote_message_contains_prices():
    """Test that analysis message contains relevant price information"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    result = engine.analyze_quote("tomato", 115.0, market_data)
    
    # Message should contain both prices
    assert "115.00" in result.message
    assert "100.00" in result.message
    assert "₹" in result.message  # Should use rupee symbol


def test_get_price_range_message():
    """Test generation of price range message"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(
        commodity="onion",
        average_price=25.0,
        min_price=20.0,
        max_price=30.0
    )
    
    message = engine.get_price_range_message(market_data)
    
    assert "onion" in message
    assert "20.00" in message
    assert "30.00" in message
    assert "25.00" in message
    assert "10 price points" in message


def test_compare_with_range_below_minimum():
    """Test comparison when price is below market minimum"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(min_price=90.0, max_price=110.0)
    
    message = engine.compare_with_range(85.0, market_data)
    
    assert "below" in message.lower()
    assert "90.00" in message


def test_compare_with_range_above_maximum():
    """Test comparison when price is above market maximum"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(min_price=90.0, max_price=110.0)
    
    message = engine.compare_with_range(115.0, market_data)
    
    assert "above" in message.lower()
    assert "110.00" in message


def test_compare_with_range_within_range():
    """Test comparison when price is within market range"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(min_price=90.0, max_price=110.0)
    
    message = engine.compare_with_range(100.0, market_data)
    
    assert "within" in message.lower()
    assert "range" in message.lower()


def test_percentage_difference_calculation():
    """Test that percentage difference is calculated correctly"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=100.0)
    
    # Test positive difference
    result = engine.analyze_quote("tomato", 120.0, market_data)
    assert result.percentage_difference == 20.0
    
    # Test negative difference
    result = engine.analyze_quote("tomato", 80.0, market_data)
    assert result.percentage_difference == -20.0
    
    # Test zero difference
    result = engine.analyze_quote("tomato", 100.0, market_data)
    assert result.percentage_difference == 0.0


def test_edge_case_very_low_prices():
    """Test analysis with very low market prices"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=5.0, min_price=4.0, max_price=6.0)
    
    # 20% above
    result = engine.analyze_quote("commodity", 6.0, market_data)
    assert result.verdict == "high"
    
    # Fair price
    result = engine.analyze_quote("commodity", 5.0, market_data)
    assert result.verdict == "fair"


def test_edge_case_very_high_prices():
    """Test analysis with very high market prices"""
    engine = PriceComparisonEngine()
    market_data = create_market_data(average_price=1000.0, min_price=900.0, max_price=1100.0)
    
    # 15% above
    result = engine.analyze_quote("commodity", 1150.0, market_data)
    assert result.verdict == "high"
    
    # Fair price
    result = engine.analyze_quote("commodity", 1000.0, market_data)
    assert result.verdict == "fair"
