"""
Unit tests for Negotiation Context Analyzer.

Tests the analyzer's ability to extract negotiation state, detect sentiment,
and analyze relationships between trading parties.

Requirements: 9.2
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.sauda_bot.negotiation_context_analyzer import NegotiationContextAnalyzer
from app.services.sauda_bot.models import (
    Message,
    RelationshipType,
    SentimentType,
)


@pytest.fixture
def analyzer():
    """Create a negotiation context analyzer instance."""
    return NegotiationContextAnalyzer()


@pytest.fixture
def sample_messages_english():
    """Create sample messages in English."""
    user1 = uuid4()
    user2 = uuid4()
    
    return [
        Message(
            id=uuid4(),
            sender_id=user1,
            text="Hello, I have fresh tomatoes available at ₹120 per kg",
            language="en",
            timestamp=datetime.now(),
        ),
        Message(
            id=uuid4(),
            sender_id=user2,
            text="That seems a bit high. Can you do ₹100 per kg?",
            language="en",
            timestamp=datetime.now(),
        ),
        Message(
            id=uuid4(),
            sender_id=user1,
            text="I can offer ₹110 per kg as my best price",
            language="en",
            timestamp=datetime.now(),
        ),
    ]


@pytest.fixture
def sample_messages_hindi():
    """Create sample messages in Hindi."""
    user1 = uuid4()
    user2 = uuid4()
    
    return [
        Message(
            id=uuid4(),
            sender_id=user1,
            text="भाई साहब, मेरे पास ताजा टमाटर हैं ₹120 प्रति किलो",
            language="hi",
            timestamp=datetime.now(),
        ),
        Message(
            id=uuid4(),
            sender_id=user2,
            text="धन्यवाद, क्या आप ₹100 में दे सकते हैं?",
            language="hi",
            timestamp=datetime.now(),
        ),
    ]


@pytest.fixture
def sample_transaction_history():
    """Create sample transaction history."""
    user1 = uuid4()
    user2 = uuid4()
    user3 = uuid4()
    
    return [
        {
            'buyer_id': user1,
            'seller_id': user2,
            'commodity': 'tomato',
            'completed_at': datetime.now() - timedelta(days=10),
        },
        {
            'buyer_id': user1,
            'seller_id': user2,
            'commodity': 'onion',
            'completed_at': datetime.now() - timedelta(days=5),
        },
        {
            'buyer_id': user1,
            'seller_id': user3,
            'commodity': 'potato',
            'completed_at': datetime.now() - timedelta(days=3),
        },
    ]


class TestNegotiationStateExtraction:
    """Test suite for negotiation state extraction"""
    
    def test_extract_negotiation_state_basic(self, analyzer, sample_messages_english):
        """Test basic negotiation state extraction"""
        state = analyzer.extract_negotiation_state(sample_messages_english)
        
        assert state.commodity == "tomatoes"
        assert state.initial_quote == 120.0
        assert len(state.counter_offers) == 2
        assert 100.0 in state.counter_offers
        assert 110.0 in state.counter_offers
        assert state.current_price == 110.0
        assert state.sentiment in [SentimentType.FRIENDLY, SentimentType.FORMAL, SentimentType.NEUTRAL]
        assert len(state.messages) == 3
    
    def test_extract_negotiation_state_empty_conversation(self, analyzer):
        """Test extraction with empty conversation"""
        with pytest.raises(ValueError, match="Conversation cannot be empty"):
            analyzer.extract_negotiation_state([])
    
    def test_extract_negotiation_state_single_message(self, analyzer):
        """Test extraction with single message"""
        message = Message(
            id=uuid4(),
            sender_id=uuid4(),
            text="I have onions at Rs.50 per kg",
            language="en",
            timestamp=datetime.now(),
        )
        
        state = analyzer.extract_negotiation_state([message])
        
        assert state.commodity == "onions"
        assert state.initial_quote == 50.0
        assert len(state.counter_offers) == 0
        assert state.current_price == 50.0
    
    def test_extract_negotiation_state_no_prices(self, analyzer):
        """Test extraction when no prices are mentioned"""
        message = Message(
            id=uuid4(),
            sender_id=uuid4(),
            text="Do you have tomatoes available?",
            language="en",
            timestamp=datetime.now(),
        )
        
        state = analyzer.extract_negotiation_state([message])
        
        assert state.commodity == "tomatoes"
        assert state.initial_quote == 0.0
        assert len(state.counter_offers) == 0
        assert state.current_price == 0.0
    
    def test_extract_negotiation_state_hindi(self, analyzer, sample_messages_hindi):
        """Test extraction with Hindi messages"""
        state = analyzer.extract_negotiation_state(sample_messages_hindi)
        
        assert state.commodity == "टमाटर"
        assert state.initial_quote == 120.0
        assert 100.0 in state.counter_offers
        assert state.sentiment == SentimentType.FRIENDLY  # Contains "भाई साहब" and "धन्यवाद"


class TestCommodityExtraction:
    """Test suite for commodity extraction"""
    
    def test_extract_commodity_english(self, analyzer):
        """Test commodity extraction in English"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I have fresh tomatoes for sale",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        commodity = analyzer._extract_commodity(messages)
        assert commodity == "tomatoes"
    
    def test_extract_commodity_hindi(self, analyzer):
        """Test commodity extraction in Hindi"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="मेरे पास प्याज है",
                language="hi",
                timestamp=datetime.now(),
            )
        ]
        
        commodity = analyzer._extract_commodity(messages)
        assert commodity == "प्याज"
    
    def test_extract_commodity_telugu(self, analyzer):
        """Test commodity extraction in Telugu"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="నా దగ్గర బంగాళాదుంప ఉంది",
                language="te",
                timestamp=datetime.now(),
            )
        ]
        
        commodity = analyzer._extract_commodity(messages)
        assert commodity == "బంగాళాదుంప"
    
    def test_extract_commodity_unknown(self, analyzer):
        """Test commodity extraction when commodity is not recognized"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I have some items for sale",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        commodity = analyzer._extract_commodity(messages)
        assert commodity == "unknown"
    
    def test_extract_commodity_multiple_commodities(self, analyzer):
        """Test commodity extraction when multiple commodities are mentioned"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I have tomatoes and onions",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        commodity = analyzer._extract_commodity(messages)
        # Should return the first match
        assert commodity in ["tomatoes", "onions"]


class TestPriceExtraction:
    """Test suite for price quote extraction"""
    
    def test_extract_quotes_rupee_symbol(self, analyzer):
        """Test price extraction with rupee symbol"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Price is ₹100 per kg",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        quotes = analyzer._extract_quotes(messages)
        assert 100.0 in quotes
    
    def test_extract_quotes_rs_abbreviation(self, analyzer):
        """Test price extraction with Rs. abbreviation"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Price is Rs.150 per kg",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        quotes = analyzer._extract_quotes(messages)
        assert 150.0 in quotes
    
    def test_extract_quotes_rupees_word(self, analyzer):
        """Test price extraction with 'rupees' word"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I can offer 200 rupees per kg",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        quotes = analyzer._extract_quotes(messages)
        assert 200.0 in quotes
    
    def test_extract_quotes_decimal_prices(self, analyzer):
        """Test price extraction with decimal values"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Best price is ₹99.50 per kg",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        quotes = analyzer._extract_quotes(messages)
        assert 99.50 in quotes
    
    def test_extract_quotes_multiple_prices(self, analyzer):
        """Test extraction of multiple prices from conversation"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I can offer ₹120 per kg",
                language="en",
                timestamp=datetime.now(),
            ),
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="How about Rs.100?",
                language="en",
                timestamp=datetime.now(),
            ),
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Final offer: 110 rupees",
                language="en",
                timestamp=datetime.now(),
            ),
        ]
        
        quotes = analyzer._extract_quotes(messages)
        assert len(quotes) == 3
        assert 120.0 in quotes
        assert 100.0 in quotes
        assert 110.0 in quotes
    
    def test_extract_quotes_filters_unrealistic_prices(self, analyzer):
        """Test that unrealistic prices are filtered out"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="In 2024, the price is ₹100 per kg",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        quotes = analyzer._extract_quotes(messages)
        # Should not include 2024 as a price
        assert 2024.0 not in quotes
        assert 100.0 in quotes
    
    def test_extract_quotes_no_prices(self, analyzer):
        """Test extraction when no prices are present"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Do you have tomatoes?",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        quotes = analyzer._extract_quotes(messages)
        assert len(quotes) == 0


class TestSentimentDetection:
    """Test suite for sentiment detection"""
    
    def test_detect_sentiment_friendly_english(self, analyzer):
        """Test friendly sentiment detection in English"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Thank you, my friend! I appreciate your offer.",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.FRIENDLY
    
    def test_detect_sentiment_friendly_hindi(self, analyzer):
        """Test friendly sentiment detection in Hindi"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="धन्यवाद भाई साहब, आप बहुत अच्छे हैं",
                language="hi",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.FRIENDLY
    
    def test_detect_sentiment_formal_english(self, analyzer):
        """Test formal sentiment detection in English"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Respected Sir, I would like to discuss this business deal.",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.FORMAL
    
    def test_detect_sentiment_formal_hindi(self, analyzer):
        """Test formal sentiment detection in Hindi"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="महोदय जी, यह व्यापार के बारे में है",
                language="hi",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.FORMAL
    
    def test_detect_sentiment_tense_english(self, analyzer):
        """Test tense sentiment detection in English"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="No, that's impossible! The price is too high and unfair.",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.TENSE
    
    def test_detect_sentiment_tense_hindi(self, analyzer):
        """Test tense sentiment detection in Hindi"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="नहीं, यह बहुत ज्यादा है! असंभव है।",
                language="hi",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.TENSE
    
    def test_detect_sentiment_neutral(self, analyzer):
        """Test neutral sentiment detection"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="I have tomatoes at 100 rupees per kg.",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        assert sentiment == SentimentType.NEUTRAL
    
    def test_detect_sentiment_empty_messages(self, analyzer):
        """Test sentiment detection with empty messages"""
        sentiment = analyzer.detect_sentiment([])
        assert sentiment == SentimentType.NEUTRAL
    
    def test_detect_sentiment_mixed_signals(self, analyzer):
        """Test sentiment detection with mixed signals"""
        messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Thank you sir, but this price is too high.",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        
        sentiment = analyzer.detect_sentiment(messages)
        # Should pick the dominant sentiment
        assert sentiment in [SentimentType.FRIENDLY, SentimentType.FORMAL, SentimentType.TENSE]


class TestRelationshipAnalysis:
    """Test suite for relationship analysis"""
    
    def test_analyze_relationship_new_customer(self, analyzer):
        """Test relationship analysis for new customer"""
        user1 = uuid4()
        user2 = uuid4()
        
        context = analyzer.analyze_relationship(user1, user2, transaction_history=[])
        
        assert context.relationship_type == RelationshipType.NEW_CUSTOMER
        assert context.transaction_count == 0
        assert context.last_transaction_date is None
    
    def test_analyze_relationship_repeat_customer(self, analyzer, sample_transaction_history):
        """Test relationship analysis for repeat customer"""
        user1 = sample_transaction_history[0]['buyer_id']
        user2 = sample_transaction_history[0]['seller_id']
        
        context = analyzer.analyze_relationship(user1, user2, sample_transaction_history)
        
        assert context.relationship_type == RelationshipType.REPEAT_CUSTOMER
        assert context.transaction_count == 2
        assert context.last_transaction_date is not None
    
    def test_analyze_relationship_frequent_partner(self, analyzer):
        """Test relationship analysis for frequent partner"""
        user1 = uuid4()
        user2 = uuid4()
        
        # Create 5+ transactions
        history = [
            {
                'buyer_id': user1,
                'seller_id': user2,
                'commodity': 'tomato',
                'completed_at': datetime.now() - timedelta(days=i),
            }
            for i in range(6)
        ]
        
        context = analyzer.analyze_relationship(user1, user2, history)
        
        assert context.relationship_type == RelationshipType.FREQUENT_PARTNER
        assert context.transaction_count == 6
        assert context.last_transaction_date is not None
    
    def test_analyze_relationship_no_history_provided(self, analyzer):
        """Test relationship analysis when no history is provided"""
        user1 = uuid4()
        user2 = uuid4()
        
        context = analyzer.analyze_relationship(user1, user2)
        
        assert context.relationship_type == RelationshipType.NEW_CUSTOMER
        assert context.transaction_count == 0
        assert context.last_transaction_date is None
    
    def test_analyze_relationship_filters_other_parties(self, analyzer, sample_transaction_history):
        """Test that relationship analysis only counts relevant transactions"""
        user1 = sample_transaction_history[0]['buyer_id']
        user3 = sample_transaction_history[2]['seller_id']
        
        context = analyzer.analyze_relationship(user1, user3, sample_transaction_history)
        
        # Should only count the one transaction between user1 and user3
        assert context.transaction_count == 1
        assert context.relationship_type == RelationshipType.REPEAT_CUSTOMER
    
    def test_analyze_relationship_bidirectional(self, analyzer):
        """Test that relationship analysis works in both directions"""
        user1 = uuid4()
        user2 = uuid4()
        
        history = [
            {
                'buyer_id': user1,
                'seller_id': user2,
                'commodity': 'tomato',
                'completed_at': datetime.now() - timedelta(days=5),
            },
            {
                'buyer_id': user2,
                'seller_id': user1,
                'commodity': 'onion',
                'completed_at': datetime.now() - timedelta(days=3),
            },
        ]
        
        # Test both directions
        context1 = analyzer.analyze_relationship(user1, user2, history)
        context2 = analyzer.analyze_relationship(user2, user1, history)
        
        assert context1.transaction_count == 2
        assert context2.transaction_count == 2
        assert context1.relationship_type == context2.relationship_type
    
    def test_analyze_relationship_last_transaction_date(self, analyzer):
        """Test that last transaction date is correctly identified"""
        user1 = uuid4()
        user2 = uuid4()
        
        recent_date = datetime.now() - timedelta(days=1)
        older_date = datetime.now() - timedelta(days=10)
        
        history = [
            {
                'buyer_id': user1,
                'seller_id': user2,
                'commodity': 'tomato',
                'completed_at': older_date,
            },
            {
                'buyer_id': user1,
                'seller_id': user2,
                'commodity': 'onion',
                'completed_at': recent_date,
            },
        ]
        
        context = analyzer.analyze_relationship(user1, user2, history)
        
        assert context.last_transaction_date == recent_date


class TestRequirements:
    """Test suite for specific requirements validation"""
    
    def test_requirement_9_2_extract_negotiation_state(self, analyzer, sample_messages_english):
        """
        Test that negotiation state extraction works correctly.
        
        Requirements: 9.2 - Extract negotiation state from conversation
        """
        state = analyzer.extract_negotiation_state(sample_messages_english)
        
        # Verify all required components are extracted
        assert state.commodity is not None
        assert state.initial_quote > 0
        assert isinstance(state.counter_offers, list)
        assert state.current_price > 0
        assert isinstance(state.sentiment, SentimentType)
        assert len(state.messages) > 0
    
    def test_requirement_9_2_analyze_relationship(self, analyzer):
        """
        Test that relationship analysis works correctly.
        
        Requirements: 9.2 - Analyze user relationship
        """
        user1 = uuid4()
        user2 = uuid4()
        
        # Test with no history
        context = analyzer.analyze_relationship(user1, user2)
        assert context.relationship_type == RelationshipType.NEW_CUSTOMER
        
        # Test with some history
        history = [
            {
                'buyer_id': user1,
                'seller_id': user2,
                'commodity': 'tomato',
                'completed_at': datetime.now(),
            }
        ]
        context = analyzer.analyze_relationship(user1, user2, history)
        assert context.relationship_type == RelationshipType.REPEAT_CUSTOMER
    
    def test_requirement_9_2_detect_sentiment(self, analyzer):
        """
        Test that sentiment detection works correctly.
        
        Requirements: 9.2 - Implement sentiment detection
        """
        # Test friendly sentiment
        friendly_messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Thank you friend, I appreciate your help!",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        assert analyzer.detect_sentiment(friendly_messages) == SentimentType.FRIENDLY
        
        # Test formal sentiment
        formal_messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="Respected Sir, let's discuss this business matter.",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        assert analyzer.detect_sentiment(formal_messages) == SentimentType.FORMAL
        
        # Test tense sentiment
        tense_messages = [
            Message(
                id=uuid4(),
                sender_id=uuid4(),
                text="No! This is impossible and too high!",
                language="en",
                timestamp=datetime.now(),
            )
        ]
        assert analyzer.detect_sentiment(tense_messages) == SentimentType.TENSE
