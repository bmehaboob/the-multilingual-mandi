# Negotiation Context Analyzer Implementation

## Overview

The `NegotiationContextAnalyzer` is a key component of the Sauda Bot negotiation assistant. It analyzes conversation context to extract negotiation state, detect sentiment, and analyze relationships between trading parties.

**Task**: 11.2 Create `NegotiationContextAnalyzer`  
**Requirements**: 9.2

## Features Implemented

### 1. Negotiation State Extraction
Extracts comprehensive negotiation state from conversation messages:
- **Commodity identification**: Detects commodity names in multiple languages (English, Hindi, Telugu, Tamil)
- **Price quote extraction**: Identifies all price mentions using various formats (₹, Rs., rupees, per kg)
- **Quote tracking**: Maintains initial quote, counter offers, and current price
- **Sentiment analysis**: Determines conversation tone (friendly, formal, tense, neutral)

### 2. Relationship Analysis
Analyzes the relationship between trading parties:
- **New Customer**: No previous transactions
- **Repeat Customer**: 1-4 previous transactions
- **Frequent Partner**: 5+ previous transactions
- Tracks transaction count and last transaction date
- Bidirectional relationship detection

### 3. Sentiment Detection
Rule-based sentiment detection using multilingual keywords:
- **Friendly**: Keywords like "friend", "thank", "भाई", "धन्यवाद", "అన్నయ్య"
- **Formal**: Keywords like "sir", "respected", "साहब", "గారు"
- **Tense**: Keywords like "no", "impossible", "नहीं", "కాదు"
- **Neutral**: Default when no strong sentiment indicators present

## Implementation Details

### File Structure
```
backend/app/services/sauda_bot/
├── negotiation_context_analyzer.py  # Main implementation
├── models.py                         # Data models
└── __init__.py                       # Module exports

backend/tests/
└── test_negotiation_context_analyzer.py  # Comprehensive unit tests
```

### Key Methods

#### `extract_negotiation_state(conversation: List[Message]) -> NegotiationState`
Extracts complete negotiation state from conversation:
```python
analyzer = NegotiationContextAnalyzer()
state = analyzer.extract_negotiation_state(messages)

# Returns:
# - commodity: str
# - initial_quote: float
# - counter_offers: List[float]
# - current_price: float
# - sentiment: SentimentType
# - messages: List[Message]
```

#### `analyze_relationship(user_id, other_party_id, transaction_history) -> RelationshipContext`
Analyzes relationship between trading parties:
```python
context = analyzer.analyze_relationship(user1_id, user2_id, history)

# Returns:
# - relationship_type: RelationshipType
# - transaction_count: int
# - last_transaction_date: Optional[datetime]
```

#### `detect_sentiment(messages: List[Message]) -> SentimentType`
Detects conversation sentiment:
```python
sentiment = analyzer.detect_sentiment(messages)

# Returns: FRIENDLY, FORMAL, TENSE, or NEUTRAL
```

## Multilingual Support

### Supported Languages
- **English**: Full support for commodity names and sentiment keywords
- **Hindi**: टमाटर, प्याज, भाई साहब, धन्यवाद, etc.
- **Telugu**: టమాటో, ఉల్లిపాయ, అన్నయ్య, గారు, etc.
- **Tamil**: தக்காளி, வெங்காயம், நண்பர், etc.

### Commodity Detection
Supports both singular and plural forms:
- tomato/tomatoes
- onion/onions
- potato/potatoes
- And equivalents in Hindi, Telugu, Tamil

### Price Formats
Recognizes multiple price formats:
- ₹100 per kg
- Rs.100
- 100 rupees
- 100.50 (decimal prices)

## Usage Example

```python
from datetime import datetime
from uuid import uuid4
from app.services.sauda_bot import NegotiationContextAnalyzer
from app.services.sauda_bot.models import Message

# Create analyzer
analyzer = NegotiationContextAnalyzer()

# Sample conversation
messages = [
    Message(
        id=uuid4(),
        sender_id=uuid4(),
        text="Hello, I have fresh tomatoes at ₹120 per kg",
        language="en",
        timestamp=datetime.now(),
    ),
    Message(
        id=uuid4(),
        sender_id=uuid4(),
        text="Thank you! Can you do ₹100 per kg?",
        language="en",
        timestamp=datetime.now(),
    ),
    Message(
        id=uuid4(),
        sender_id=uuid4(),
        text="I can offer ₹110 per kg as my best price",
        language="en",
        timestamp=datetime.now(),
    ),
]

# Extract negotiation state
state = analyzer.extract_negotiation_state(messages)

print(f"Commodity: {state.commodity}")
print(f"Initial Quote: ₹{state.initial_quote}")
print(f"Counter Offers: {state.counter_offers}")
print(f"Current Price: ₹{state.current_price}")
print(f"Sentiment: {state.sentiment}")

# Output:
# Commodity: tomatoes
# Initial Quote: ₹120.0
# Counter Offers: [100.0, 110.0]
# Current Price: ₹110.0
# Sentiment: FRIENDLY

# Analyze relationship
user1 = uuid4()
user2 = uuid4()

transaction_history = [
    {
        'buyer_id': user1,
        'seller_id': user2,
        'commodity': 'tomato',
        'completed_at': datetime.now(),
    }
]

relationship = analyzer.analyze_relationship(user1, user2, transaction_history)

print(f"Relationship: {relationship.relationship_type}")
print(f"Transaction Count: {relationship.transaction_count}")

# Output:
# Relationship: REPEAT_CUSTOMER
# Transaction Count: 1
```

## Integration with Sauda Bot

The `NegotiationContextAnalyzer` is designed to work seamlessly with other Sauda Bot components:

1. **LLM Service**: Provides context for generating culturally-aware negotiation suggestions
2. **Cultural Context Engine**: Sentiment and relationship data inform cultural adaptation
3. **Suggestion Generator**: Uses negotiation state to generate appropriate counter-offers

### Typical Workflow
```python
# 1. Analyze conversation context
analyzer = NegotiationContextAnalyzer()
negotiation_state = analyzer.extract_negotiation_state(conversation)
relationship_context = analyzer.analyze_relationship(user_id, other_party_id, history)

# 2. Get cultural context (from CulturalContextEngine)
cultural_context = cultural_engine.get_context(language, region, relationship_context)

# 3. Get market data (from Fair Price Oracle)
market_data = price_oracle.get_price_aggregation(negotiation_state.commodity)

# 4. Generate suggestion (from LLM Service)
suggestion = llm_service.generate_counter_offer(
    negotiation_state,
    market_data,
    cultural_context
)
```

## Test Coverage

### Unit Tests (36 tests, all passing)
- **Negotiation State Extraction**: 5 tests
- **Commodity Extraction**: 5 tests
- **Price Extraction**: 7 tests
- **Sentiment Detection**: 9 tests
- **Relationship Analysis**: 7 tests
- **Requirements Validation**: 3 tests

### Test Categories
1. **Basic functionality**: Core extraction and analysis
2. **Edge cases**: Empty conversations, missing data, unknown commodities
3. **Multilingual support**: Hindi, Telugu, Tamil
4. **Price formats**: Various currency notations
5. **Sentiment detection**: All sentiment types across languages
6. **Relationship types**: New, repeat, and frequent customers

## Performance Characteristics

- **Extraction Speed**: O(n) where n is number of messages
- **Memory Usage**: Minimal - only stores extracted data
- **Scalability**: Can handle conversations with hundreds of messages
- **Language Support**: Extensible pattern-based approach

## Future Enhancements

Potential improvements for future iterations:
1. **ML-based sentiment analysis**: Replace rule-based with trained models
2. **More languages**: Add support for remaining Indian languages
3. **Context-aware extraction**: Use conversation flow for better accuracy
4. **Entity linking**: Connect commodity mentions across messages
5. **Confidence scoring**: Add confidence metrics to extractions

## Requirements Validation

✅ **Requirement 9.2**: Sentiment Analysis
- Analyzes sentiment of previous messages in conversation
- Detects friendly, formal, and tense tones
- Supports multilingual sentiment keywords

✅ **Requirement 9.2**: Relationship Analysis
- Determines new vs. repeat customer relationships
- Tracks transaction count and history
- Adapts to relationship context

✅ **Requirement 9.2**: Negotiation State Extraction
- Extracts commodity, quotes, and prices
- Maintains negotiation history
- Provides complete context for suggestion generation

## Conclusion

The `NegotiationContextAnalyzer` successfully implements all required functionality for task 11.2. It provides robust, multilingual context analysis that enables the Sauda Bot to generate culturally-aware and contextually-appropriate negotiation suggestions.

All 36 unit tests pass, demonstrating comprehensive coverage of functionality and edge cases. The implementation is ready for integration with other Sauda Bot components.
