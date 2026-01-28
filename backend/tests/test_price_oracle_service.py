"""
Tests for Price Oracle Service

Tests price data aggregation and comparison functionality.
Requirements: 6.3, 7.5
"""
import pytest
from app.services.price_oracle.price_data_aggregator import PriceDataAggregator
from app.services.price_oracle.price_comparison_engine import PriceComparisonEngine
from app.services.price_oracle.models import Location


class TestPriceDataAggregator:
    """Test suite for price data aggregator"""
    
    @pytest.mark.asyncio
    async def test_aggregate_prices_success(self):
        """Test successful price aggregation"""
        aggregator = PriceDataAggregator()
        location = Location(state="Maharashtra", district="Pune")
        
        result = await aggregator.aggregate_prices("tomato", location)
        
        # Verify result structure
        assert result.commodity == "tomato"
        assert result.location.state == "Maharashtra"
        assert result.min_price > 0
        assert result.max_price > 0
        assert result.average_price > 0
        assert result.sample_size > 0
        assert len(result.sources_used) > 0
        
        # Verify price relationships
        assert result.min_price <= result.average_price <= result.max_price
    
    @pytest.mark.asyncio
    async def test_aggregate_prices_different_states(self):
        """Test price aggregation for different states"""
        aggregator = PriceDataAggregator()
        
        # Get prices for Maharashtra
        location_mh = Location(state="Maharashtra")
        result_mh = await aggregator.aggregate_prices("tomato", location_mh)
        
        # Get prices for Karnataka
        location_ka = Location(state="Karnataka")
        result_ka = await aggregator.aggregate_prices("tomato", location_ka)
        
        # Prices should be different due to regional variations
        assert result_mh.average_price != result_ka.average_price
    
    @pytest.mark.asyncio
    async def test_aggregate_prices_response_time(self):
        """Test that price aggregation completes within 3 seconds (Requirement 6.3)"""
        import time
        
        aggregator = PriceDataAggregator()
        location = Location(state="Maharashtra")
        
        start_time = time.time()
        result = await aggregator.aggregate_prices("tomato", location)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert result is not None
        assert response_time < 3.0, f"Response time {response_time}s exceeds 3 second requirement"
    
    @pytest.mark.asyncio
    async def test_data_source_indicators(self):
        """Test that data sources are clearly indicated (Requirement 7.5)"""
        aggregator = PriceDataAggregator()
        location = Location(state="Maharashtra")
        
        result = await aggregator.aggregate_prices("tomato", location)
        
        # Verify sources_used is present and contains valid sources
        assert len(result.sources_used) > 0
        
        valid_sources = ["enam", "mandi_board", "crowd_sourced", "demo"]
        for source in result.sources_used:
            assert source.value in valid_sources


class TestPriceComparisonEngine:
    """Test suite for price comparison engine"""
    
    @pytest.mark.asyncio
    async def test_analyze_quote_fair(self):
        """Test price analysis for fair price"""
        aggregator = PriceDataAggregator()
        engine = PriceComparisonEngine()
        location = Location(state="Maharashtra")
        
        # Get market data
        market_data = await aggregator.aggregate_prices("tomato", location)
        
        # Test with a price close to average (within 5%)
        quoted_price = market_data.average_price * 1.03  # 3% above average
        
        analysis = engine.analyze_quote("tomato", quoted_price, market_data)
        
        assert analysis.verdict == "fair"
        assert analysis.quoted_price == quoted_price
        assert analysis.market_average == market_data.average_price
        assert abs(analysis.percentage_difference) <= 5.0
    
    @pytest.mark.asyncio
    async def test_analyze_quote_high(self):
        """Test price analysis for high price"""
        aggregator = PriceDataAggregator()
        engine = PriceComparisonEngine()
        location = Location(state="Maharashtra")
        
        # Get market data
        market_data = await aggregator.aggregate_prices("tomato", location)
        
        # Test with a price significantly above average (>10%)
        quoted_price = market_data.average_price * 1.15  # 15% above average
        
        analysis = engine.analyze_quote("tomato", quoted_price, market_data)
        
        assert analysis.verdict == "high"
        assert analysis.percentage_difference > 10.0
    
    @pytest.mark.asyncio
    async def test_analyze_quote_low(self):
        """Test price analysis for low price"""
        aggregator = PriceDataAggregator()
        engine = PriceComparisonEngine()
        location = Location(state="Maharashtra")
        
        # Get market data
        market_data = await aggregator.aggregate_prices("tomato", location)
        
        # Test with a price significantly below average (>10%)
        quoted_price = market_data.average_price * 0.85  # 15% below average
        
        analysis = engine.analyze_quote("tomato", quoted_price, market_data)
        
        assert analysis.verdict == "low"
        assert analysis.percentage_difference < -10.0
    
    @pytest.mark.asyncio
    async def test_price_range_message(self):
        """Test price range message generation"""
        aggregator = PriceDataAggregator()
        engine = PriceComparisonEngine()
        location = Location(state="Maharashtra")
        
        # Get market data
        market_data = await aggregator.aggregate_prices("tomato", location)
        
        # Get price range message
        message = engine.get_price_range_message(market_data)
        
        assert "tomato" in message.lower()
        assert str(market_data.min_price) in message
        assert str(market_data.max_price) in message
        assert str(market_data.average_price) in message
