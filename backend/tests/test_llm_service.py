"""
Unit tests for LLM Service.

Tests the LLM service for loading models and generating negotiation suggestions.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.services.sauda_bot.llm_service import LLMService
from app.services.sauda_bot.models import (
    CulturalContext,
    FestivalContext,
    Message,
    NegotiationState,
    NegotiationStyle,
    PriceAggregation,
    RelationshipContext,
    RelationshipType,
    SentimentType,
)


@pytest.fixture
def mock_negotiation_state():
    """Create a mock negotiation state for testing."""
    return NegotiationState(
        commodity="tomato",
        initial_quote=120.0,
        counter_offers=[110.0],
        current_price=120.0,
        sentiment=SentimentType.FRIENDLY,
        messages=[
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I can offer tomatoes at 120 rupees per kg",
                language="en",
                timestamp=datetime.now(),
            )
        ],
    )


@pytest.fixture
def mock_market_data():
    """Create mock market price data."""
    return PriceAggregation(
        commodity="tomato",
        min_price=90.0,
        max_price=110.0,
        average_price=100.0,
        median_price=100.0,
        std_dev=5.0,
        sample_size=10,
        timestamp=datetime.now(),
    )


@pytest.fixture
def mock_cultural_context():
    """Create mock cultural context."""
    return CulturalContext(
        language="en",
        region="Maharashtra",
        honorifics=["Sir", "Madam"],
        relationship_terms=["valued customer", "respected trader"],
        negotiation_style=NegotiationStyle.RELATIONSHIP_FOCUSED,
        festival_context=None,
    )


@pytest.fixture
def mock_cultural_context_with_festival():
    """Create mock cultural context with festival."""
    return CulturalContext(
        language="hi",
        region="Maharashtra",
        honorifics=["भाई साहब", "जी"],
        relationship_terms=["valued customer", "respected trader"],
        negotiation_style=NegotiationStyle.RELATIONSHIP_FOCUSED,
        festival_context=FestivalContext(
            festival_name="Diwali",
            date=datetime.now(),
            typical_price_adjustment=1.15,
        ),
    )


class TestLLMService:
    """Test suite for LLM Service"""
    
    def test_initialization_default(self):
        """Test LLM service initialization with defaults"""
        service = LLMService()
        
        assert service.model_name == "llama-3.1-8b"
        assert service.use_quantization is True
        assert service.device in ["cuda", "cpu"]
        assert service.model is None  # Lazy loading
        assert service.tokenizer is None
    
    def test_initialization_custom_model(self):
        """Test LLM service initialization with custom model"""
        service = LLMService(model_name="mistral-7b")
        
        assert service.model_name == "mistral-7b"
        assert service._get_model_id() == "mistralai/Mistral-7B-Instruct-v0.3"
    
    def test_initialization_invalid_model(self):
        """Test LLM service initialization with invalid model"""
        service = LLMService(model_name="invalid-model")
        
        with pytest.raises(ValueError, match="Unsupported model"):
            service._get_model_id()
    
    def test_get_model_id_llama(self):
        """Test getting model ID for Llama"""
        service = LLMService(model_name="llama-3.1-8b")
        model_id = service._get_model_id()
        
        assert model_id == "meta-llama/Meta-Llama-3.1-8B-Instruct"
    
    def test_get_model_id_mistral(self):
        """Test getting model ID for Mistral"""
        service = LLMService(model_name="mistral-7b")
        model_id = service._get_model_id()
        
        assert model_id == "mistralai/Mistral-7B-Instruct-v0.3"
    
    def test_prompt_templates_loaded(self):
        """Test that prompt templates are loaded"""
        service = LLMService()
        
        assert "counter_offer" in service.prompt_templates
        assert "Commodity:" in service.prompt_templates["counter_offer"]
        assert "Market Average:" in service.prompt_templates["counter_offer"]
    
    def test_build_prompt_basic(
        self,
        mock_negotiation_state,
        mock_market_data,
        mock_cultural_context,
    ):
        """Test building a basic prompt"""
        service = LLMService()
        
        prompt = service._build_prompt(
            mock_negotiation_state,
            mock_market_data,
            mock_cultural_context,
        )
        
        # Check that key information is in the prompt
        assert "tomato" in prompt.lower()
        assert "120" in prompt  # Current price
        assert "100" in prompt  # Market average
        assert "Maharashtra" in prompt
        assert "friendly" in prompt.lower()
        assert "Sir" in prompt or "Madam" in prompt
    
    def test_build_prompt_with_festival(
        self,
        mock_negotiation_state,
        mock_market_data,
        mock_cultural_context_with_festival,
    ):
        """Test building a prompt with festival context"""
        service = LLMService()
        
        prompt = service._build_prompt(
            mock_negotiation_state,
            mock_market_data,
            mock_cultural_context_with_festival,
        )
        
        # Check that festival information is included
        assert "Diwali" in prompt
        assert "1.15" in prompt or "15%" in prompt
    
    def test_extract_suggestion_valid_output(self):
        """Test extracting suggestion from well-formed LLM output"""
        service = LLMService()
        
        generated_text = """
SUGGESTED_PRICE: 105.50
MESSAGE: Respected Sir, considering the current market conditions, I would like to propose ₹105.50 per kg.
"""
        
        suggestion = service._extract_suggestion(generated_text, market_average=100.0)
        
        assert suggestion.suggested_price == 105.50
        assert "Respected Sir" in suggestion.message
        assert suggestion.confidence > 0.5
    
    def test_extract_suggestion_missing_price(self):
        """Test extracting suggestion when price is missing"""
        service = LLMService()
        
        generated_text = """
MESSAGE: Let's discuss a fair price for the tomatoes.
"""
        
        suggestion = service._extract_suggestion(generated_text, market_average=100.0)
        
        # Should fallback to market average
        assert suggestion.suggested_price == 100.0
        assert suggestion.confidence < 0.8
    
    def test_extract_suggestion_price_out_of_bounds(self):
        """Test that extracted price is clamped to 15% of market average"""
        service = LLMService()
        
        # Price way above market average
        generated_text = """
SUGGESTED_PRICE: 200.00
MESSAGE: This is a very high price.
"""
        
        suggestion = service._extract_suggestion(generated_text, market_average=100.0)
        
        # Should be clamped to max 115 (15% above 100)
        assert suggestion.suggested_price <= 115.0
        assert suggestion.suggested_price >= 85.0
    
    def test_extract_suggestion_price_below_bounds(self):
        """Test that extracted price is clamped when too low"""
        service = LLMService()
        
        # Price way below market average
        generated_text = """
SUGGESTED_PRICE: 50.00
MESSAGE: This is a very low price.
"""
        
        suggestion = service._extract_suggestion(generated_text, market_average=100.0)
        
        # Should be clamped to min 85 (15% below 100)
        assert suggestion.suggested_price >= 85.0
        assert suggestion.suggested_price <= 115.0
    
    def test_counter_offer_bounds_requirement(
        self,
        mock_negotiation_state,
        mock_market_data,
        mock_cultural_context,
    ):
        """
        Test that counter-offers are within 15% of market average.
        
        Requirements: 8.2
        """
        service = LLMService()
        
        # Mock the model to avoid actual loading
        service.model = "mock"
        service.tokenizer = "mock"
        
        # Test the price bounds logic in _extract_suggestion
        market_avg = mock_market_data.average_price
        
        # Test various prices
        test_prices = [50.0, 85.0, 100.0, 115.0, 200.0]
        
        for price in test_prices:
            generated_text = f"SUGGESTED_PRICE: {price}\nMESSAGE: Test message"
            suggestion = service._extract_suggestion(generated_text, market_avg)
            
            # Verify price is within bounds
            min_price = market_avg * 0.85
            max_price = market_avg * 1.15
            
            assert suggestion.suggested_price >= min_price
            assert suggestion.suggested_price <= max_price
    
    def test_unload_model(self):
        """Test unloading model from memory"""
        service = LLMService()
        
        # Set mock model and tokenizer
        service.model = "mock_model"
        service.tokenizer = "mock_tokenizer"
        
        service.unload_model()
        
        assert service.model is None
        assert service.tokenizer is None


class TestLLMServiceIntegration:
    """
    Integration tests for LLM Service.
    
    These tests are marked as slow and may be skipped in CI.
    They require actual model downloads and GPU/CPU inference.
    """
    
    @pytest.mark.slow
    @pytest.mark.skipif(
        True,  # Skip by default to avoid long test times
        reason="Requires model download and inference (slow)",
    )
    def test_generate_counter_offer_integration(
        self,
        mock_negotiation_state,
        mock_market_data,
        mock_cultural_context,
    ):
        """
        Integration test for generating counter-offer with real model.
        
        This test is skipped by default as it requires:
        - Downloading the model (~8GB)
        - GPU or significant CPU resources
        - Several seconds to minutes for inference
        
        To run: pytest -m slow tests/test_llm_service.py
        """
        service = LLMService(
            model_name="llama-3.1-8b",
            use_quantization=True,
        )
        
        suggestion = service.generate_counter_offer(
            mock_negotiation_state,
            mock_market_data,
            mock_cultural_context,
        )
        
        # Verify suggestion structure
        assert suggestion.suggested_price > 0
        assert len(suggestion.message) > 0
        assert len(suggestion.rationale) > 0
        assert 0 <= suggestion.confidence <= 1.0
        
        # Verify price bounds (Requirement 8.2)
        market_avg = mock_market_data.average_price
        assert suggestion.suggested_price >= market_avg * 0.85
        assert suggestion.suggested_price <= market_avg * 1.15
        
        service.unload_model()
