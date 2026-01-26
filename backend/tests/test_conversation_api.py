"""Unit tests for conversation management API"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.conversation import Conversation, Message, ConversationStatus
from app.core.security import create_access_token

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_conversation_api.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client"""
    def override_get_db_for_test():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db_for_test
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_users(client, db_session):
    """Create test users"""
    user1 = User(
        id=uuid.uuid4(),
        name="Test User 1",
        phone_number="+1234567890",
        primary_language="en",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    user2 = User(
        id=uuid.uuid4(),
        name="Test User 2",
        phone_number="+1234567891",
        primary_language="hi",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    user3 = User(
        id=uuid.uuid4(),
        name="Test User 3",
        phone_number="+1234567892",
        primary_language="te",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    
    db_session.add_all([user1, user2, user3])
    db_session.commit()
    
    return {"user1": user1, "user2": user2, "user3": user3}


@pytest.fixture
def auth_headers(test_users):
    """Create authentication headers for test users"""
    user1_token = create_access_token({"sub": str(test_users["user1"].id)})
    user2_token = create_access_token({"sub": str(test_users["user2"].id)})
    user3_token = create_access_token({"sub": str(test_users["user3"].id)})
    
    return {
        "user1": {"Authorization": f"Bearer {user1_token}"},
        "user2": {"Authorization": f"Bearer {user2_token}"},
        "user3": {"Authorization": f"Bearer {user3_token}"}
    }


# Test: Create conversation
def test_create_conversation_success(client, db_session, test_users, auth_headers):
    """Test creating a conversation successfully"""
    response = client.post(
        "/api/v1/conversations",
        json={
            "participant_ids": [str(test_users["user1"].id), str(test_users["user2"].id)],
            "commodity": "tomato"
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert len(data["participants"]) == 2
    assert data["commodity"] == "tomato"
    assert data["status"] == "active"
    assert data["message_count"] == 0


def test_create_conversation_without_current_user(client, db_session, test_users, auth_headers):
    """Test creating a conversation without including current user fails"""
    response = client.post(
        "/api/v1/conversations",
        json={
            "participant_ids": [str(test_users["user2"].id), str(test_users["user3"].id)],
            "commodity": "onion"
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 400
    assert "must be included" in response.json()["detail"].lower()


def test_create_conversation_max_limit(client, db_session, test_users, auth_headers):
    """Test creating more than 5 concurrent conversations fails"""
    # Create 5 active conversations
    for i in range(5):
        response = client.post(
            "/api/v1/conversations",
            json={
                "participant_ids": [str(test_users["user1"].id), str(test_users["user2"].id)],
                "commodity": f"commodity_{i}"
            },
            headers=auth_headers["user1"]
        )
        assert response.status_code == 201
    
    # Try to create 6th conversation
    response = client.post(
        "/api/v1/conversations",
        json={
            "participant_ids": [str(test_users["user1"].id), str(test_users["user2"].id)],
            "commodity": "commodity_6"
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 400
    assert "maximum" in response.json()["detail"].lower()


def test_create_conversation_with_nonexistent_user(client, db_session, test_users, auth_headers):
    """Test creating a conversation with non-existent user fails"""
    fake_user_id = str(uuid.uuid4())
    
    response = client.post(
        "/api/v1/conversations",
        json={
            "participant_ids": [str(test_users["user1"].id), fake_user_id],
            "commodity": "wheat"
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


# Test: List conversations
def test_list_conversations_empty(client, db_session, test_users, auth_headers):
    """Test listing conversations when user has none"""
    response = client.get(
        "/api/v1/conversations",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["active_count"] == 0
    assert len(data["conversations"]) == 0


def test_list_conversations_with_data(client, db_session, test_users, auth_headers):
    """Test listing conversations with existing data"""
    # Create conversations
    conv1 = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        commodity="tomato",
        status=ConversationStatus.ACTIVE
    )
    conv2 = Conversation(
        participants=[test_users["user1"].id, test_users["user3"].id],
        commodity="onion",
        status=ConversationStatus.COMPLETED
    )
    
    db_session.add_all([conv1, conv2])
    db_session.commit()
    
    response = client.get(
        "/api/v1/conversations",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["active_count"] == 1
    assert len(data["conversations"]) == 2


def test_list_conversations_with_status_filter(client, db_session, test_users, auth_headers):
    """Test listing conversations with status filter"""
    # Create conversations
    conv1 = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    conv2 = Conversation(
        participants=[test_users["user1"].id, test_users["user3"].id],
        status=ConversationStatus.COMPLETED
    )
    
    db_session.add_all([conv1, conv2])
    db_session.commit()
    
    # Filter by active
    response = client.get(
        "/api/v1/conversations?status_filter=active",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["conversations"][0]["status"] == "active"


# Test: Get specific conversation
def test_get_conversation_success(client, db_session, test_users, auth_headers):
    """Test getting a specific conversation"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        commodity="rice",
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/{conv.id}",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(conv.id)
    assert data["commodity"] == "rice"
    assert data["status"] == "active"


def test_get_conversation_not_participant(client, db_session, test_users, auth_headers):
    """Test getting a conversation where user is not a participant"""
    conv = Conversation(
        participants=[test_users["user2"].id, test_users["user3"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/{conv.id}",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 403
    assert "not a participant" in response.json()["detail"].lower()


def test_get_conversation_not_found(client, db_session, test_users, auth_headers):
    """Test getting a non-existent conversation"""
    fake_id = str(uuid.uuid4())
    
    response = client.get(
        f"/api/v1/conversations/{fake_id}",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# Test: Update conversation
def test_update_conversation_commodity(client, db_session, test_users, auth_headers):
    """Test updating conversation commodity"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        commodity="tomato",
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.patch(
        f"/api/v1/conversations/{conv.id}",
        json={"commodity": "potato"},
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["commodity"] == "potato"


def test_update_conversation_status(client, db_session, test_users, auth_headers):
    """Test updating conversation status"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.patch(
        f"/api/v1/conversations/{conv.id}",
        json={"status": "completed"},
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_update_conversation_invalid_status(client, db_session, test_users, auth_headers):
    """Test updating conversation with invalid status"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.patch(
        f"/api/v1/conversations/{conv.id}",
        json={"status": "invalid_status"},
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 400


# Test: End conversation
def test_end_conversation_completed(client, db_session, test_users, auth_headers):
    """Test ending a conversation with completed status"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.post(
        f"/api/v1/conversations/{conv.id}/end?final_status=completed",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["final_status"] == "completed"


def test_end_conversation_abandoned(client, db_session, test_users, auth_headers):
    """Test ending a conversation with abandoned status"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.post(
        f"/api/v1/conversations/{conv.id}/end?final_status=abandoned",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["final_status"] == "abandoned"


# Test: Send message
def test_send_message_success(client, db_session, test_users, auth_headers):
    """Test sending a message successfully"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={
            "original_text": "Hello, how much for tomatoes?",
            "original_language": "en",
            "translated_text": {"hi": "नमस्ते, टमाटर के लिए कितना?"},
            "message_metadata": {"transcription_confidence": 0.95}
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["original_text"] == "Hello, how much for tomatoes?"
    assert data["original_language"] == "en"
    assert "hi" in data["translated_text"]


def test_send_message_to_inactive_conversation(client, db_session, test_users, auth_headers):
    """Test sending a message to an inactive conversation fails"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.COMPLETED
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={
            "original_text": "Test message",
            "original_language": "en"
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 403
    assert "cannot send message" in response.json()["detail"].lower()


def test_send_message_not_participant(client, db_session, test_users, auth_headers):
    """Test sending a message when not a participant fails"""
    conv = Conversation(
        participants=[test_users["user2"].id, test_users["user3"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.post(
        f"/api/v1/conversations/{conv.id}/messages",
        json={
            "original_text": "Test message",
            "original_language": "en"
        },
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 403


# Test: Get messages
def test_get_messages_empty(client, db_session, test_users, auth_headers):
    """Test getting messages from a conversation with no messages"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/{conv.id}/messages",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["messages"]) == 0


def test_get_messages_with_data(client, db_session, test_users, auth_headers):
    """Test getting messages from a conversation with messages"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    # Add messages
    msg1 = Message(
        conversation_id=conv.id,
        sender_id=test_users["user1"].id,
        original_text="Hello",
        original_language="en"
    )
    msg2 = Message(
        conversation_id=conv.id,
        sender_id=test_users["user2"].id,
        original_text="नमस्ते",
        original_language="hi"
    )
    
    db_session.add_all([msg1, msg2])
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/{conv.id}/messages",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["messages"]) == 2


def test_get_messages_with_pagination(client, db_session, test_users, auth_headers):
    """Test getting messages with pagination"""
    conv = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    # Add 5 messages
    for i in range(5):
        msg = Message(
            conversation_id=conv.id,
            sender_id=test_users["user1"].id,
            original_text=f"Message {i}",
            original_language="en"
        )
        db_session.add(msg)
    db_session.commit()
    
    # Get first 2 messages
    response = client.get(
        f"/api/v1/conversations/{conv.id}/messages?limit=2&offset=0",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["messages"]) == 2


def test_get_messages_not_participant(client, db_session, test_users, auth_headers):
    """Test getting messages when not a participant fails"""
    conv = Conversation(
        participants=[test_users["user2"].id, test_users["user3"].id],
        status=ConversationStatus.ACTIVE
    )
    db_session.add(conv)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/conversations/{conv.id}/messages",
        headers=auth_headers["user1"]
    )
    
    assert response.status_code == 403


# Test: Conversation context isolation
def test_conversation_context_isolation(client, db_session, test_users, auth_headers):
    """Test that conversations maintain separate contexts"""
    # Create two conversations
    conv1 = Conversation(
        participants=[test_users["user1"].id, test_users["user2"].id],
        commodity="tomato",
        status=ConversationStatus.ACTIVE
    )
    conv2 = Conversation(
        participants=[test_users["user1"].id, test_users["user3"].id],
        commodity="onion",
        status=ConversationStatus.ACTIVE
    )
    
    db_session.add_all([conv1, conv2])
    db_session.commit()
    
    # Send messages to each conversation
    msg1 = Message(
        conversation_id=conv1.id,
        sender_id=test_users["user1"].id,
        original_text="Message for conv1",
        original_language="en"
    )
    msg2 = Message(
        conversation_id=conv2.id,
        sender_id=test_users["user1"].id,
        original_text="Message for conv2",
        original_language="en"
    )
    
    db_session.add_all([msg1, msg2])
    db_session.commit()
    
    # Get messages from conv1
    response1 = client.get(
        f"/api/v1/conversations/{conv1.id}/messages",
        headers=auth_headers["user1"]
    )
    
    # Get messages from conv2
    response2 = client.get(
        f"/api/v1/conversations/{conv2.id}/messages",
        headers=auth_headers["user1"]
    )
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Verify messages are isolated
    assert data1["total"] == 1
    assert data2["total"] == 1
    assert data1["messages"][0]["original_text"] == "Message for conv1"
    assert data2["messages"][0]["original_text"] == "Message for conv2"


# Test: Health check
def test_conversation_health_check(client):
    """Test conversation service health check"""
    response = client.get("/api/v1/conversations/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "conversations"
    assert data["max_concurrent_conversations"] == 5
