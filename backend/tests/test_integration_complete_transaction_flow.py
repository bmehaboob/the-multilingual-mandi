"""
Integration Test 21.1: Complete Transaction Flow
Tests Hindi speaker negotiating with Telugu speaker

This test validates the complete end-to-end flow:
- Voice translation between Hindi and Telugu
- Price checking with Fair Price Oracle
- Negotiation assistance from Sauda Bot
- Transaction completion

Requirements: 1.1, 3.1, 5.1, 7.1, 8.1
"""
import pytest
import numpy as np
from uuid import uuid4
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.conversation import Conversation, Message, ConversationStatus
from app.models.transaction import Transaction
from app.services.vocal_vernacular.vocal_vernacular_engine import VocalVernacularEngine
from app.services.price_oracle.price_data_aggregator import PriceDataAggregator
from app.services.price_oracle.price_comparison_engine import PriceComparisonEngine
from app.services.sauda_bot.suggestion_generator import SuggestionGenerator
from app.services.sauda_bot.negotiation_context_analyzer import NegotiationContextAnalyzer
from app.services.sauda_bot.cultural_context_engine import CulturalContextEngine
from app.services.transaction_service import TransactionService


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_integration_transaction.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def hindi_speaker(db_session):
    """Create a Hindi-speaking user (buyer)"""
    user = User(
        id=uuid4(),
        name="राज कुमार",
        phone_number="+919876543210",
        primary_language="hin",
        location_state="Maharashtra",
        location_district="Mumbai",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def telugu_speaker(db_session):
    """Create a Telugu-speaking user (seller)"""
    user = User(
        id=uuid4(),
        name="వెంకట రావు",
        phone_number="+919876543211",
        primary_language="tel",
        location_state="Andhra Pradesh",
        location_district="Guntur",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def conversation(db_session, hindi_speaker, telugu_speaker):
    """Create a conversation between Hindi and Telugu speakers"""
    conv = Conversation(
        id=uuid4(),
        participants=[hindi_speaker.id, telugu_speaker.id],
        commodity="tomato",
        status=ConversationStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(conv)
    db_session.commit()
    return conv


@pytest.fixture
def vve():
    """Create Vocal Vernacular Engine with mock services"""
    return VocalVernacularEngine(use_mock=True)


@pytest.fixture
def price_aggregator():
    """Create Price Data Aggregator"""
    return PriceDataAggregator(use_demo_data=True)


@pytest.fixture
def price_engine():
    """Create Price Comparison Engine"""
    return PriceComparisonEngine()


@pytest.fixture
def suggestion_generator():
    """Create Suggestion Generator"""
    return SuggestionGenerator(use_mock=True)


@pytest.fixture
def negotiation_analyzer():
    """Create Negotiation Context Analyzer"""
    return NegotiationContextAnalyzer()


@pytest.fixture
def cultural_engine():
    """Create Cultural Context Engine"""
    return CulturalContextEngine()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_transaction_flow_hindi_to_telugu(
    db_session,
    hindi_speaker,
    telugu_speaker,
    conversation,
    vve,
    price_aggregator,
    price_engine,
    suggestion_generator,
    negotiation_analyzer,
    cultural_engine
):
    """
    Integration Test: Complete transaction flow from Hindi speaker to Telugu speaker
    
    Scenario:
    1. Hindi buyer asks about tomato prices (voice)
    2. System translates to Telugu for seller
    3. Telugu seller quotes a price (voice)
    4. System translates to Hindi and checks price fairness
    5. Hindi buyer requests negotiation help
    6. System provides culturally-appropriate counter-offer suggestion
    7. Negotiation continues
    8. Transaction is completed
    """
    
    # Step 1: Hindi buyer asks about tomato prices
    # Simulate Hindi audio: "टमाटर का भाव क्या है?"
    hindi_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    buyer_message_1 = await vve.process_voice_message(
        audio=hindi_audio,
        target_language="tel",  # Translate to Telugu for seller
        source_language="hin",
        auto_detect_language=False
    )
    
    # Verify translation completed
    assert buyer_message_1 is not None
    assert buyer_message_1.source_language == "hin"
    assert buyer_message_1.target_language == "tel"
    assert buyer_message_1.latency_ms < 8000  # Requirement 5.1
    
    # Store message in conversation
    msg1 = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        sender_id=hindi_speaker.id,
        original_text=buyer_message_1.transcription,
        original_language="hin",
        translated_text={"tel": buyer_message_1.translation},
        timestamp=datetime.utcnow()
    )
    db_session.add(msg1)
    db_session.commit()
    
    # Step 2: Check current market price for tomatoes
    price_data = await price_aggregator.aggregate_prices(
        commodity="tomato",
        state="Maharashtra"
    )
    
    assert price_data is not None
    assert price_data.average_price > 0
    assert price_data.commodity == "tomato"
    
    # Step 3: Telugu seller quotes a price (30 Rs/kg)
    # Simulate Telugu audio: "టమాటా కిలో ముప్పై రూపాయలు"
    telugu_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    seller_message_1 = await vve.process_voice_message(
        audio=telugu_audio,
        target_language="hin",  # Translate to Hindi for buyer
        source_language="tel",
        auto_detect_language=False
    )
    
    # Verify translation completed
    assert seller_message_1 is not None
    assert seller_message_1.source_language == "tel"
    assert seller_message_1.target_language == "hin"
    assert seller_message_1.latency_ms < 8000  # Requirement 5.1
    
    # Store message
    msg2 = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        sender_id=telugu_speaker.id,
        original_text=seller_message_1.transcription,
        original_language="tel",
        translated_text={"hin": seller_message_1.translation},
        timestamp=datetime.utcnow()
    )
    db_session.add(msg2)
    db_session.commit()
    
    # Step 4: Check if quoted price is fair
    quoted_price = 30.0  # Rs/kg
    
    price_analysis = price_engine.analyze_quote(
        commodity="tomato",
        quoted_price=quoted_price,
        market_data=price_data
    )
    
    assert price_analysis is not None
    assert price_analysis.verdict in ["fair", "high", "low"]
    assert price_analysis.message is not None
    
    # Step 5: Hindi buyer requests negotiation help
    # Get conversation history for context
    conversation_messages = db_session.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.timestamp).all()
    
    # Analyze negotiation context
    negotiation_state = negotiation_analyzer.extract_negotiation_state(
        conversation_messages=conversation_messages,
        commodity="tomato",
        quoted_price=quoted_price
    )
    
    assert negotiation_state is not None
    assert negotiation_state.commodity == "tomato"
    assert negotiation_state.current_quote == quoted_price
    
    # Get cultural context for Hindi-Telugu negotiation
    cultural_context = cultural_engine.get_cultural_context(
        language="hin",
        region="Maharashtra",
        relationship_type="new_customer"
    )
    
    assert cultural_context is not None
    assert len(cultural_context.honorifics) > 0
    
    # Step 6: Generate culturally-appropriate counter-offer
    suggestion = await suggestion_generator.generate_counter_offer(
        negotiation_state=negotiation_state,
        market_data=price_data,
        cultural_context=cultural_context,
        language="hin"
    )
    
    assert suggestion is not None
    assert suggestion.suggested_price is not None
    assert suggestion.message is not None
    
    # Verify counter-offer is within 15% of market average (Requirement 8.2)
    market_avg = price_data.average_price
    price_diff_percent = abs(suggestion.suggested_price - market_avg) / market_avg * 100
    assert price_diff_percent <= 15, f"Counter-offer {suggestion.suggested_price} is {price_diff_percent:.1f}% from market average {market_avg}"
    
    # Verify suggestion includes cultural honorifics (Requirement 9.1)
    assert any(honorific in suggestion.message for honorific in cultural_context.honorifics)
    
    # Step 7: Buyer sends counter-offer using suggestion
    counter_offer_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    buyer_message_2 = await vve.process_voice_message(
        audio=counter_offer_audio,
        target_language="tel",
        source_language="hin",
        auto_detect_language=False
    )
    
    msg3 = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        sender_id=hindi_speaker.id,
        original_text=buyer_message_2.transcription,
        original_language="hin",
        translated_text={"tel": buyer_message_2.translation},
        timestamp=datetime.utcnow()
    )
    db_session.add(msg3)
    db_session.commit()
    
    # Step 8: Seller accepts counter-offer
    seller_acceptance_audio = np.random.randn(16000).astype(np.float32) * 0.1
    
    seller_message_2 = await vve.process_voice_message(
        audio=seller_acceptance_audio,
        target_language="hin",
        source_language="tel",
        auto_detect_language=False
    )
    
    msg4 = Message(
        id=uuid4(),
        conversation_id=conversation.id,
        sender_id=telugu_speaker.id,
        original_text=seller_message_2.transcription,
        original_language="tel",
        translated_text={"hin": seller_message_2.translation},
        timestamp=datetime.utcnow()
    )
    db_session.add(msg4)
    db_session.commit()
    
    # Step 9: Complete transaction
    transaction_service = TransactionService()
    
    agreed_price = suggestion.suggested_price
    quantity = 10.0  # kg
    
    success, transaction, error = transaction_service.create_transaction(
        db=db_session,
        buyer_id=str(hindi_speaker.id),
        seller_id=str(telugu_speaker.id),
        commodity="tomato",
        quantity=quantity,
        unit="kg",
        agreed_price=agreed_price,
        market_average_at_time=market_avg,
        conversation_id=str(conversation.id)
    )
    
    assert success is True
    assert transaction is not None
    assert error is None
    
    # Verify transaction data completeness (Requirement 13.1)
    assert transaction.commodity == "tomato"
    assert transaction.quantity == quantity
    assert transaction.unit == "kg"
    assert transaction.agreed_price == agreed_price
    assert transaction.market_average_at_time == market_avg
    assert transaction.buyer_id == hindi_speaker.id
    assert transaction.seller_id == telugu_speaker.id
    assert transaction.conversation_id == conversation.id
    assert transaction.completed_at is not None
    
    # Step 10: Mark conversation as completed
    conversation.status = ConversationStatus.COMPLETED
    conversation.updated_at = datetime.utcnow()
    db_session.commit()
    
    # Verify final state
    assert conversation.status == ConversationStatus.COMPLETED
    
    # Verify all messages were stored
    final_message_count = db_session.query(Message).filter(
        Message.conversation_id == conversation.id
    ).count()
    assert final_message_count == 4
    
    print("\n✓ Complete transaction flow test passed!")
    print(f"  - Voice translation latency: {buyer_message_1.latency_ms:.0f}ms")
    print(f"  - Market average price: ₹{market_avg:.2f}/kg")
    print(f"  - Quoted price: ₹{quoted_price:.2f}/kg")
    print(f"  - Price verdict: {price_analysis.verdict}")
    print(f"  - Suggested counter-offer: ₹{suggestion.suggested_price:.2f}/kg")
    print(f"  - Final agreed price: ₹{agreed_price:.2f}/kg")
    print(f"  - Transaction completed successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_flow_with_price_rejection(
    db_session,
    hindi_speaker,
    telugu_speaker,
    conversation,
    vve,
    price_aggregator,
    price_engine
):
    """
    Test transaction flow where buyer rejects high price and walks away
    """
    # Get market price
    price_data = await price_aggregator.aggregate_prices(
        commodity="tomato",
        state="Maharashtra"
    )
    
    # Seller quotes very high price (50% above market)
    quoted_price = price_data.average_price * 1.5
    
    # Check price fairness
    price_analysis = price_engine.analyze_quote(
        commodity="tomato",
        quoted_price=quoted_price,
        market_data=price_data
    )
    
    # Should be classified as "high"
    assert price_analysis.verdict == "high"
    
    # Buyer decides to abandon conversation
    conversation.status = ConversationStatus.ABANDONED
    db_session.commit()
    
    # Verify no transaction was created
    transaction_count = db_session.query(Transaction).filter(
        Transaction.conversation_id == conversation.id
    ).count()
    assert transaction_count == 0
    
    print("\n✓ Price rejection flow test passed!")
    print(f"  - Market average: ₹{price_data.average_price:.2f}/kg")
    print(f"  - Quoted price: ₹{quoted_price:.2f}/kg (50% above market)")
    print(f"  - Verdict: {price_analysis.verdict}")
    print(f"  - Conversation abandoned without transaction")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_flow_performance(
    db_session,
    hindi_speaker,
    telugu_speaker,
    conversation,
    vve,
    price_aggregator,
    price_engine,
    suggestion_generator,
    negotiation_analyzer,
    cultural_engine
):
    """
    Test that complete transaction flow meets performance requirements
    """
    import time
    
    start_time = time.time()
    
    # Simulate complete flow
    # 1. Voice translation (buyer question)
    audio1 = np.random.randn(16000).astype(np.float32) * 0.1
    msg1 = await vve.process_voice_message(audio1, "tel", "hin", False)
    
    # 2. Price check
    price_data = await price_aggregator.aggregate_prices("tomato", "Maharashtra")
    
    # 3. Voice translation (seller quote)
    audio2 = np.random.randn(16000).astype(np.float32) * 0.1
    msg2 = await vve.process_voice_message(audio2, "hin", "tel", False)
    
    # 4. Price analysis
    price_analysis = price_engine.analyze_quote("tomato", 30.0, price_data)
    
    # 5. Negotiation suggestion
    negotiation_state = negotiation_analyzer.extract_negotiation_state(
        conversation_messages=[],
        commodity="tomato",
        quoted_price=30.0
    )
    cultural_context = cultural_engine.get_cultural_context("hin", "Maharashtra", "new_customer")
    suggestion = await suggestion_generator.generate_counter_offer(
        negotiation_state, price_data, cultural_context, "hin"
    )
    
    # 6. Voice translation (counter-offer)
    audio3 = np.random.randn(16000).astype(np.float32) * 0.1
    msg3 = await vve.process_voice_message(audio3, "tel", "hin", False)
    
    # 7. Transaction creation
    transaction_service = TransactionService()
    success, transaction, error = transaction_service.create_transaction(
        db=db_session,
        buyer_id=str(hindi_speaker.id),
        seller_id=str(telugu_speaker.id),
        commodity="tomato",
        quantity=10.0,
        unit="kg",
        agreed_price=suggestion.suggested_price,
        market_average_at_time=price_data.average_price
    )
    
    end_time = time.time()
    total_time_ms = (end_time - start_time) * 1000
    
    # Verify all operations succeeded
    assert msg1 is not None
    assert msg2 is not None
    assert msg3 is not None
    assert price_data is not None
    assert price_analysis is not None
    assert suggestion is not None
    assert success is True
    
    # Verify individual latencies
    assert msg1.latency_ms < 8000  # Voice translation < 8s
    assert msg2.latency_ms < 8000
    assert msg3.latency_ms < 8000
    
    print("\n✓ Transaction flow performance test passed!")
    print(f"  - Total flow time: {total_time_ms:.0f}ms")
    print(f"  - Voice translation 1: {msg1.latency_ms:.0f}ms")
    print(f"  - Voice translation 2: {msg2.latency_ms:.0f}ms")
    print(f"  - Voice translation 3: {msg3.latency_ms:.0f}ms")
    print(f"  - All operations completed successfully")
