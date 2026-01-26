"""
Unit tests for SuggestionGenerator.

Tests the orchestration of LLM service, cultural context engine, and
negotiation context analyzer for generating culturally-appropriate suggestions.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.services.sauda_bot.suggestion_generator import SuggestionGenerator
from app.services.sauda_bot.models import (
    Message,
    NegotiationSuggestion,
    PriceAggregation,
)


@pytest.fixture
def suggestion_generator():
    """Create a SuggestionGenerator instance for testing."""
    return SuggestionGenerator()


@pytest.fixture
def sample_conversation():
    """Create a sample conversation for testing."""
    user_id = uuid4()
    other_party_id = uuid4()
    
    return [
        Message(
            id=uuid4(),
            sender_id=other_party_id,
            text="I can sell you tomatoes at 30 rupees per kg",
            language="en",
            timestamp=datetime.now()
        ),
        Message(
            id=uuid4(),
            sender_id=user_id,
            text="That seems a bit high. What is your best price?",
            language="en",
            timestamp=datetime.now()
        ),
    ]


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    return PriceAggregation(
        commodity="tomato",
        min_price=18.0,
        max_price=28.0,
        average_price=23.0,
        median_price=23.0,
        std_dev=2.5,
        sample_size=10,
        timestamp=datetime.now()
    )


class TestPriceBoundsValidation:
    """Test price bounds validation (Requirement 8.2)."""
    
    def test_price_within_bounds_unchanged(self, suggestion_generator):
        """Test that prices within 15% of market average are unchanged."""
        market_avg = 100.0
        suggested_price = 110.0
        
        validated = suggestion_generator._validate_price_bounds(
            suggested_price,
            market_avg
        )
        
        assert validated == suggested_price
    
    def test_price_above_upper_bound_clamped(self, suggestion_generator):
        """Test that prices >15% above market average are clamped."""
        market_avg = 100.0
        suggested_price = 120.0
        
        validated = suggestion_generator._validate_price_bounds(
            suggested_price,
            market_avg
        )
        
        # Use approximate comparison for floating point
        assert abs(validated - 115.0) < 0.01
    
    def test_price_below_lower_bound_clamped(self, suggestion_generator):
        """Test that prices >15% below market average are clamped."""
        market_avg = 100.0
        suggested_price = 80.0
        
        validated = suggestion_generator._validate_price_bounds(
            suggested_price,
            market_avg
        )
        
        assert validated == 85.0


class TestAggressiveLanguageFiltering:
    """Test aggressive language filtering (Requirement 9.5)."""
    
    def test_no_aggressive_language_unchanged(self, suggestion_generator):
        """Test that polite messages are unchanged."""
        message = "I would like to discuss a fair price for the tomatoes."
        
        filtered = suggestion_generator._filter_aggressive_language(message)
        
        assert filtered == message
    
    def test_english_aggressive_terms_filtered(self, suggestion_generator):
        """Test that English aggressive terms are filtered."""
        message = "You are trying to cheat me with this ridiculous price!"
        
        filtered = suggestion_generator._filter_aggressive_language(message)
        
        assert "cheat" not in filtered.lower()
        assert "ridiculous" not in filtered.lower()
        assert "fair price" in filtered.lower()


class TestHonorificInclusion:
    """Test honorific inclusion (Requirement 9.1)."""
    
    def test_message_with_honorific_unchanged(self, suggestion_generator):
        """Test that messages with honorifics are unchanged."""
        message = "Sir, can we discuss the price?"
        honorifics = ["Sir", "Madam"]
        relationship_terms = ["friend", "partner"]
        
        result = suggestion_generator._ensure_honorifics(
            message,
            honorifics,
            relationship_terms
        )
        
        assert result == message
    
    def test_message_without_honorific_gets_one(self, suggestion_generator):
        """Test that messages without honorifics get one added."""
        message = "Can we discuss the price?"
        honorifics = ["Sir", "Madam"]
        relationship_terms = ["friend", "partner"]
        
        result = suggestion_generator._ensure_honorifics(
            message,
            honorifics,
            relationship_terms
        )
        
        assert result.startswith("Sir,")
        assert "Can we discuss the price?" in result


class TestCounterOfferGeneration:
    """Test complete counter-offer generation."""
    
    def test_generate_counter_offer_basic(
        self,
        suggestion_generator,
        sample_conversation,
        sample_market_data
    ):
        """Test basic counter-offer generation."""
        user_id = uuid4()
        other_party_id = uuid4()
        
        suggestion = suggestion_generator.generate_counter_offer(
            conversation=sample_conversation,
            market_data=sample_market_data,
            user_id=user_id,
            other_party_id=other_party_id,
            language="en",
            region="Maharashtra"
        )
        
        assert isinstance(suggestion, NegotiationSuggestion)
        assert suggestion.suggested_price > 0
        assert len(suggestion.message) > 0
        
        market_avg = sample_market_data.average_price
        assert suggestion.suggested_price >= market_avg * 0.85
        assert suggestion.suggested_price <= market_avg * 1.15


class TestHistoricalFallback:
    """Test historical price fallback (Requirement 8.5)."""
    
    def test_fallback_without_market_data_uses_historical(
        self,
        suggestion_generator,
        sample_conversation
    ):
        """Test that historical prices are used when market data unavailable."""
        user_id = uuid4()
        other_party_id = uuid4()
        historical_prices = [20.0, 22.0, 24.0, 21.0, 23.0]
        historical_avg = sum(historical_prices) / len(historical_prices)
        
        suggestion = suggestion_generator.generate_counter_offer_with_historical_fallback(
            conversation=sample_conversation,
            market_data=None,
            historical_prices=historical_prices,
            user_id=user_id,
            other_party_id=other_party_id,
            language="en",
            region="Maharashtra"
        )
        
        assert suggestion.suggested_price >= historical_avg * 0.85
        assert suggestion.suggested_price <= historical_avg * 1.15
