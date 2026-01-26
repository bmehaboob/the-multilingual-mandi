"""Unit tests for Conversation, Message, and Transaction models"""
import pytest
import uuid
from datetime import datetime
from app.models import Conversation, Message, Transaction
from app.models.conversation import ConversationStatus


class TestConversationModel:
    """Test Conversation model"""
    
    def test_conversation_creation(self):
        """Test creating a Conversation instance"""
        conv_id = uuid.uuid4()
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        conversation = Conversation(
            id=conv_id,
            participants=[user1_id, user2_id],
            commodity="tomato",
            status=ConversationStatus.ACTIVE
        )
        
        assert conversation.id == conv_id
        assert len(conversation.participants) == 2
        assert user1_id in conversation.participants
        assert user2_id in conversation.participants
        assert conversation.commodity == "tomato"
        assert conversation.status == ConversationStatus.ACTIVE
    
    def test_conversation_repr(self):
        """Test Conversation string representation"""
        conv_id = uuid.uuid4()
        conversation = Conversation(
            id=conv_id,
            participants=[uuid.uuid4(), uuid.uuid4()],
            status=ConversationStatus.ACTIVE
        )
        
        assert repr(conversation) == f"<Conversation {conv_id} (ConversationStatus.ACTIVE)>"
    
    def test_conversation_with_minimal_fields(self):
        """Test Conversation with only required fields"""
        conversation = Conversation(
            id=uuid.uuid4(),
            participants=[uuid.uuid4(), uuid.uuid4()],
            status=ConversationStatus.ACTIVE
        )
        
        assert len(conversation.participants) == 2
        assert conversation.commodity is None
        assert conversation.status == ConversationStatus.ACTIVE
    
    def test_conversation_status_enum(self):
        """Test all ConversationStatus enum values"""
        conv_id = uuid.uuid4()
        participants = [uuid.uuid4(), uuid.uuid4()]
        
        # Test ACTIVE status
        conv_active = Conversation(
            id=conv_id,
            participants=participants,
            status=ConversationStatus.ACTIVE
        )
        assert conv_active.status == ConversationStatus.ACTIVE
        assert conv_active.status.value == "active"
        
        # Test COMPLETED status
        conv_completed = Conversation(
            id=uuid.uuid4(),
            participants=participants,
            status=ConversationStatus.COMPLETED
        )
        assert conv_completed.status == ConversationStatus.COMPLETED
        assert conv_completed.status.value == "completed"
        
        # Test ABANDONED status
        conv_abandoned = Conversation(
            id=uuid.uuid4(),
            participants=participants,
            status=ConversationStatus.ABANDONED
        )
        assert conv_abandoned.status == ConversationStatus.ABANDONED
        assert conv_abandoned.status.value == "abandoned"
    
    def test_conversation_multiple_participants(self):
        """Test Conversation with multiple participants"""
        participants = [uuid.uuid4() for _ in range(5)]
        
        conversation = Conversation(
            id=uuid.uuid4(),
            participants=participants,
            status=ConversationStatus.ACTIVE
        )
        
        assert len(conversation.participants) == 5
        for participant_id in participants:
            assert participant_id in conversation.participants
    
    def test_conversation_with_commodity(self):
        """Test Conversation with commodity specified"""
        conversation = Conversation(
            id=uuid.uuid4(),
            participants=[uuid.uuid4(), uuid.uuid4()],
            commodity="onion",
            status=ConversationStatus.ACTIVE
        )
        
        assert conversation.commodity == "onion"


class TestMessageModel:
    """Test Message model"""
    
    def test_message_creation(self):
        """Test creating a Message instance"""
        msg_id = uuid.uuid4()
        conv_id = uuid.uuid4()
        sender_id = uuid.uuid4()
        
        message = Message(
            id=msg_id,
            conversation_id=conv_id,
            sender_id=sender_id,
            original_text="मैं टमाटर खरीदना चाहता हूं",
            original_language="hi",
            translated_text={"en": "I want to buy tomatoes", "te": "నేను టమోటాలు కొనాలనుకుంటున్నాను"},
            audio_url="https://storage.example.com/audio/msg123.mp3",
            message_metadata={
                "transcription_confidence": 0.95,
                "translation_confidence": 0.92,
                "latency_ms": 7500
            }
        )
        
        assert message.id == msg_id
        assert message.conversation_id == conv_id
        assert message.sender_id == sender_id
        assert message.original_text == "मैं टमाटर खरीदना चाहता हूं"
        assert message.original_language == "hi"
        assert message.translated_text["en"] == "I want to buy tomatoes"
        assert message.translated_text["te"] == "నేను టమోటాలు కొనాలనుకుంటున్నాను"
        assert message.audio_url == "https://storage.example.com/audio/msg123.mp3"
        assert message.message_metadata["transcription_confidence"] == 0.95
    
    def test_message_repr(self):
        """Test Message string representation"""
        msg_id = uuid.uuid4()
        sender_id = uuid.uuid4()
        
        message = Message(
            id=msg_id,
            conversation_id=uuid.uuid4(),
            sender_id=sender_id,
            original_text="Test message",
            original_language="en"
        )
        
        assert repr(message) == f"<Message {msg_id} from {sender_id}>"
    
    def test_message_with_minimal_fields(self):
        """Test Message with only required fields"""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            sender_id=uuid.uuid4(),
            original_text="Hello",
            original_language="en"
        )
        
        assert message.original_text == "Hello"
        assert message.original_language == "en"
        # SQLAlchemy doesn't set defaults for JSONB columns when creating instances directly
        # The default is applied at the database level
        assert message.translated_text is None or message.translated_text == {}
        assert message.audio_url is None
        assert message.message_metadata is None or message.message_metadata == {}
    
    def test_message_multiple_translations(self):
        """Test Message with translations to multiple languages"""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            sender_id=uuid.uuid4(),
            original_text="How much per kg?",
            original_language="en",
            translated_text={
                "hi": "प्रति किलो कितना?",
                "te": "కిలోకు ఎంత?",
                "ta": "கிலோவுக்கு எவ்வளவு?",
                "kn": "ಪ್ರತಿ ಕೆಜಿಗೆ ಎಷ್ಟು?"
            }
        )
        
        assert len(message.translated_text) == 4
        assert "hi" in message.translated_text
        assert "te" in message.translated_text
        assert "ta" in message.translated_text
        assert "kn" in message.translated_text
    
    def test_message_metadata_structure(self):
        """Test Message metadata contains expected fields"""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            sender_id=uuid.uuid4(),
            original_text="Test",
            original_language="en",
            message_metadata={
                "transcription_confidence": 0.88,
                "translation_confidence": 0.91,
                "latency_ms": 6200,
                "noise_level_db": 65,
                "audio_duration_ms": 2500
            }
        )
        
        assert message.message_metadata["transcription_confidence"] == 0.88
        assert message.message_metadata["translation_confidence"] == 0.91
        assert message.message_metadata["latency_ms"] == 6200
        assert message.message_metadata["noise_level_db"] == 65
        assert message.message_metadata["audio_duration_ms"] == 2500
    
    def test_message_without_audio_url(self):
        """Test Message without audio URL (text-only mode)"""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            sender_id=uuid.uuid4(),
            original_text="Text only message",
            original_language="en",
            audio_url=None
        )
        
        assert message.audio_url is None


class TestTransactionModel:
    """Test Transaction model"""
    
    def test_transaction_creation(self):
        """Test creating a Transaction instance"""
        txn_id = uuid.uuid4()
        buyer_id = uuid.uuid4()
        seller_id = uuid.uuid4()
        conv_id = uuid.uuid4()
        
        transaction = Transaction(
            id=txn_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            commodity="tomato",
            quantity=50.0,
            unit="kg",
            agreed_price=25.0,
            market_average_at_time=23.5,
            conversation_id=conv_id,
            location={"state": "Maharashtra", "district": "Pune"}
        )
        
        assert transaction.id == txn_id
        assert transaction.buyer_id == buyer_id
        assert transaction.seller_id == seller_id
        assert transaction.commodity == "tomato"
        assert transaction.quantity == 50.0
        assert transaction.unit == "kg"
        assert transaction.agreed_price == 25.0
        assert transaction.market_average_at_time == 23.5
        assert transaction.conversation_id == conv_id
        assert transaction.location["state"] == "Maharashtra"
        assert transaction.location["district"] == "Pune"
    
    def test_transaction_repr(self):
        """Test Transaction string representation"""
        txn_id = uuid.uuid4()
        
        transaction = Transaction(
            id=txn_id,
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="onion",
            quantity=100.0,
            unit="kg",
            agreed_price=30.0
        )
        
        assert repr(transaction) == f"<Transaction {txn_id} - onion>"
    
    def test_transaction_with_minimal_fields(self):
        """Test Transaction with only required fields"""
        transaction = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="potato",
            quantity=75.0,
            unit="kg",
            agreed_price=18.0
        )
        
        assert transaction.commodity == "potato"
        assert transaction.quantity == 75.0
        assert transaction.unit == "kg"
        assert transaction.agreed_price == 18.0
        assert transaction.market_average_at_time is None
        assert transaction.conversation_id is None
        assert transaction.location is None
    
    def test_transaction_different_units(self):
        """Test Transaction with different units"""
        # Test kg
        txn_kg = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="rice",
            quantity=100.0,
            unit="kg",
            agreed_price=35.0
        )
        assert txn_kg.unit == "kg"
        
        # Test quintal
        txn_quintal = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="wheat",
            quantity=5.0,
            unit="quintal",
            agreed_price=2800.0
        )
        assert txn_quintal.unit == "quintal"
        
        # Test ton
        txn_ton = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="sugarcane",
            quantity=2.0,
            unit="ton",
            agreed_price=5000.0
        )
        assert txn_ton.unit == "ton"
    
    def test_transaction_price_comparison(self):
        """Test Transaction with price above and below market average"""
        # Price above market average
        txn_high = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="tomato",
            quantity=50.0,
            unit="kg",
            agreed_price=28.0,
            market_average_at_time=25.0
        )
        assert txn_high.agreed_price > txn_high.market_average_at_time
        
        # Price below market average
        txn_low = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="onion",
            quantity=100.0,
            unit="kg",
            agreed_price=22.0,
            market_average_at_time=25.0
        )
        assert txn_low.agreed_price < txn_low.market_average_at_time
    
    def test_transaction_location_structure(self):
        """Test Transaction location JSONB field structure"""
        transaction = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="potato",
            quantity=80.0,
            unit="kg",
            agreed_price=20.0,
            location={
                "state": "Karnataka",
                "district": "Bangalore",
                "mandi": "Yeshwanthpur Mandi",
                "coordinates": {
                    "latitude": 13.0289,
                    "longitude": 77.5503
                }
            }
        )
        
        assert transaction.location["state"] == "Karnataka"
        assert transaction.location["district"] == "Bangalore"
        assert transaction.location["mandi"] == "Yeshwanthpur Mandi"
        assert transaction.location["coordinates"]["latitude"] == 13.0289
        assert transaction.location["coordinates"]["longitude"] == 77.5503
    
    def test_transaction_without_conversation(self):
        """Test Transaction created without associated conversation"""
        transaction = Transaction(
            id=uuid.uuid4(),
            buyer_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            commodity="rice",
            quantity=200.0,
            unit="kg",
            agreed_price=40.0,
            conversation_id=None
        )
        
        assert transaction.conversation_id is None


class TestModelRelationships:
    """Test relationships between models"""
    
    def test_conversation_has_messages_relationship(self):
        """Test that Conversation model has messages relationship"""
        assert hasattr(Conversation, 'messages')
    
    def test_message_has_conversation_relationship(self):
        """Test that Message model has conversation relationship"""
        assert hasattr(Message, 'conversation')


class TestModelTableNames:
    """Test that table names are correct"""
    
    def test_conversation_table_name(self):
        """Test Conversation table name"""
        assert Conversation.__tablename__ == "conversations"
    
    def test_message_table_name(self):
        """Test Message table name"""
        assert Message.__tablename__ == "messages"
    
    def test_transaction_table_name(self):
        """Test Transaction table name"""
        assert Transaction.__tablename__ == "transactions"


class TestModelColumns:
    """Test that models have required columns"""
    
    def test_conversation_has_required_columns(self):
        """Test Conversation has all required columns"""
        columns = [c.name for c in Conversation.__table__.columns]
        
        required_columns = [
            'id', 'participants', 'commodity', 'status',
            'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_message_has_required_columns(self):
        """Test Message has all required columns"""
        columns = [c.name for c in Message.__table__.columns]
        
        required_columns = [
            'id', 'conversation_id', 'sender_id', 'original_text',
            'original_language', 'translated_text', 'audio_url',
            'timestamp', 'message_metadata'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_transaction_has_required_columns(self):
        """Test Transaction has all required columns"""
        columns = [c.name for c in Transaction.__table__.columns]
        
        required_columns = [
            'id', 'buyer_id', 'seller_id', 'commodity', 'quantity',
            'unit', 'agreed_price', 'market_average_at_time',
            'conversation_id', 'completed_at', 'location'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"


class TestConversationStatusEnum:
    """Test ConversationStatus enum"""
    
    def test_enum_values(self):
        """Test that ConversationStatus has correct values"""
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.COMPLETED.value == "completed"
        assert ConversationStatus.ABANDONED.value == "abandoned"
    
    def test_enum_members(self):
        """Test that ConversationStatus has all expected members"""
        members = [status.name for status in ConversationStatus]
        assert "ACTIVE" in members
        assert "COMPLETED" in members
        assert "ABANDONED" in members
        assert len(members) == 3
