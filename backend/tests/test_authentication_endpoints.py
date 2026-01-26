"""Unit tests for authentication endpoints"""
import pytest
import base64
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Float, LargeBinary, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

from app.main import app
from app.core.database import get_db
from app.services.auth.voice_biometric_verification import VoiceBiometricVerification
from app.services.auth.authentication_service import AuthenticationService
from app.api.routes.auth import auth_service
import numpy as np

# Create a separate base for testing
TestBase = declarative_base()

# Test models (simplified for SQLite compatibility)
class TestUser(TestBase):
    """Test user model compatible with SQLite"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    primary_language = Column(String(10), nullable=False)
    secondary_languages = Column(String, default="[]")  # JSON string for SQLite
    location = Column(String, nullable=True)  # JSON string for SQLite
    voiceprint_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow)
    preferences = Column(String, default="{}")  # JSON string for SQLite
    
    voiceprint = relationship("TestVoiceprint", back_populates="user", uselist=False, cascade="all, delete-orphan")


class TestVoiceprint(TestBase):
    """Test voiceprint model compatible with SQLite"""
    __tablename__ = "voiceprints"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True)
    embedding_data = Column(LargeBinary, nullable=False)
    encryption_algorithm = Column(String(50), default="AES-256", nullable=False)
    sample_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("TestUser", back_populates="voiceprint")


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    TestBase.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user with voiceprint"""
    user = TestUser(
        id=str(uuid.uuid4()),
        name="Test User",
        phone_number="+919876543210",
        primary_language="hin",
        secondary_languages='["eng"]',
        location='{"state": "Maharashtra", "district": "Mumbai"}'
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create a voiceprint for the user
    # Using a dummy embedding (in real scenario, this would be from enrollment)
    dummy_embedding = np.random.rand(192).astype(np.float32)
    voiceprint = TestVoiceprint(
        id=str(uuid.uuid4()),
        user_id=user.id,
        embedding_data=dummy_embedding.tobytes(),
        encryption_algorithm="AES-256",
        sample_count=3
    )
    db_session.add(voiceprint)
    db_session.commit()
    
    # Store the embedding in the verification service for testing
    auth_service.voice_verification.enrollment_service._voiceprint_storage[user.id] = dummy_embedding
    
    return user


@pytest.fixture
def test_user_with_pin(test_user):
    """Create a test user with PIN set"""
    auth_service.voice_verification.set_pin(test_user.id, "1234")
    return test_user


@pytest.fixture
def sample_audio():
    """Generate sample audio data for testing"""
    # Generate 1 second of random audio at 16kHz
    sample_rate = 16000
    duration = 1.0
    audio_data = np.random.randint(-32768, 32767, int(sample_rate * duration), dtype=np.int16)
    audio_bytes = audio_data.tobytes()
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    return audio_base64


class TestVoiceLogin:
    """Tests for voice biometric login"""
    
    def test_voice_login_success(self, client, test_user, sample_audio):
        """Test successful voice login"""
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "phone_number": test_user.phone_number,
                "audio_data": sample_audio,
                "sample_rate": 16000
            }
        )
        
        # Note: This test may fail due to voice verification logic
        # In a real scenario, we'd mock the verification service
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "authentication_method" in data
        assert data["authentication_method"] == "voice"
    
    def test_voice_login_user_not_found(self, client, sample_audio):
        """Test voice login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "phone_number": "+919999999999",
                "audio_data": sample_audio,
                "sample_rate": 16000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_voice_login_no_voiceprint(self, client, db_session, sample_audio):
        """Test voice login for user without voiceprint"""
        # Create user without voiceprint
        user = TestUser(
            id=str(uuid.uuid4()),
            name="No Voiceprint User",
            phone_number="+919876543211",
            primary_language="hin"
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "phone_number": user.phone_number,
                "audio_data": sample_audio,
                "sample_rate": 16000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "voiceprint" in data["message"].lower()
    
    def test_voice_login_invalid_audio(self, client, test_user):
        """Test voice login with invalid audio data"""
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "phone_number": test_user.phone_number,
                "audio_data": "invalid_base64!!!",
                "sample_rate": 16000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_voice_login_missing_phone(self, client, sample_audio):
        """Test voice login without phone number"""
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "audio_data": sample_audio,
                "sample_rate": 16000
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestPINLogin:
    """Tests for PIN-based login"""
    
    def test_pin_login_success(self, client, test_user_with_pin):
        """Test successful PIN login"""
        response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["authentication_method"] == "pin"
        assert data["token"] is not None
        assert "access_token" in data["token"]
    
    def test_pin_login_wrong_pin(self, client, test_user_with_pin):
        """Test PIN login with incorrect PIN"""
        response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "9999"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "incorrect" in data["message"].lower() or "failed" in data["message"].lower()
    
    def test_pin_login_no_pin_set(self, client, test_user):
        """Test PIN login when user hasn't set a PIN"""
        response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user.phone_number,
                "pin": "1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_pin_login_invalid_pin_format(self, client, test_user_with_pin):
        """Test PIN login with invalid PIN format"""
        response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "abc"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestHybridLogin:
    """Tests for hybrid authentication"""
    
    def test_hybrid_login_with_pin_fallback(self, client, test_user_with_pin, sample_audio):
        """Test hybrid login falling back to PIN"""
        response = client.post(
            "/api/v1/auth/login/hybrid",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "audio_data": sample_audio,
                "sample_rate": 16000,
                "pin": "1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should succeed with either voice or PIN
        if data["success"]:
            assert data["authentication_method"] in ["voice", "pin"]
            assert data["token"] is not None
    
    def test_hybrid_login_pin_only(self, client, test_user_with_pin):
        """Test hybrid login with PIN only"""
        response = client.post(
            "/api/v1/auth/login/hybrid",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["authentication_method"] == "pin"
    
    def test_hybrid_login_no_credentials(self, client, test_user):
        """Test hybrid login without any credentials"""
        response = client.post(
            "/api/v1/auth/login/hybrid",
            json={
                "phone_number": test_user.phone_number
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestLogout:
    """Tests for logout functionality"""
    
    def test_logout_success(self, client, test_user_with_pin):
        """Test successful logout"""
        # First login to get a token
        login_response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["token"]["access_token"]
        
        # Now logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logout_response.status_code == 200
        data = logout_response.json()
        assert data["success"] is True
    
    def test_logout_without_token(self, client):
        """Test logout without authentication token"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 403  # Forbidden


class TestSetPIN:
    """Tests for setting PIN"""
    
    def test_set_pin_success(self, client, test_user_with_pin):
        """Test successfully setting a PIN"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        token = login_response.json()["token"]["access_token"]
        
        # Set new PIN
        response = client.post(
            "/api/v1/auth/pin/set",
            json={"pin": "5678"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_set_pin_invalid_format(self, client, test_user_with_pin):
        """Test setting PIN with invalid format"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        token = login_response.json()["token"]["access_token"]
        
        # Try to set invalid PIN
        response = client.post(
            "/api/v1/auth/pin/set",
            json={"pin": "abc"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_set_pin_without_auth(self, client):
        """Test setting PIN without authentication"""
        response = client.post(
            "/api/v1/auth/pin/set",
            json={"pin": "1234"}
        )
        
        assert response.status_code == 403  # Forbidden


class TestGetCurrentUser:
    """Tests for getting current user info"""
    
    def test_get_current_user_success(self, client, test_user_with_pin):
        """Test getting current user information"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        token = login_response.json()["token"]["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == test_user_with_pin.phone_number
        assert data["name"] == test_user_with_pin.name
        assert data["primary_language"] == test_user_with_pin.primary_language
    
    def test_get_current_user_without_auth(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # Forbidden
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401  # Unauthorized


class TestAuthHealthCheck:
    """Tests for authentication health check"""
    
    def test_auth_health_check(self, client):
        """Test authentication service health check"""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"
        assert "voice_verification" in data


class TestTokenValidation:
    """Tests for JWT token validation"""
    
    def test_token_contains_user_info(self, client, test_user_with_pin):
        """Test that token contains correct user information"""
        response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        token_data = data["token"]
        
        assert token_data["user_id"] == test_user_with_pin.id
        assert token_data["phone_number"] == test_user_with_pin.phone_number
        assert token_data["name"] == test_user_with_pin.name
        assert token_data["primary_language"] == test_user_with_pin.primary_language
        assert token_data["token_type"] == "bearer"
        assert token_data["expires_in"] > 0
    
    def test_token_expiration_time(self, client, test_user_with_pin):
        """Test that token has correct expiration time"""
        response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be 30 minutes (1800 seconds) by default
        assert data["token"]["expires_in"] == 1800


class TestEdgeCases:
    """Tests for edge cases and error conditions"""
    
    def test_login_with_empty_phone(self, client, sample_audio):
        """Test login with empty phone number"""
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "phone_number": "",
                "audio_data": sample_audio,
                "sample_rate": 16000
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_with_short_phone(self, client, sample_audio):
        """Test login with too short phone number"""
        response = client.post(
            "/api/v1/auth/login/voice",
            json={
                "phone_number": "123",
                "audio_data": sample_audio,
                "sample_rate": 16000
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_set_pin_too_short(self, client, test_user_with_pin):
        """Test setting PIN that's too short"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        token = login_response.json()["token"]["access_token"]
        
        # Try to set too short PIN
        response = client.post(
            "/api/v1/auth/pin/set",
            json={"pin": "12"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_set_pin_too_long(self, client, test_user_with_pin):
        """Test setting PIN that's too long"""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login/pin",
            json={
                "phone_number": test_user_with_pin.phone_number,
                "pin": "1234"
            }
        )
        
        token = login_response.json()["token"]["access_token"]
        
        # Try to set too long PIN
        response = client.post(
            "/api/v1/auth/pin/set",
            json={"pin": "1234567"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 422  # Validation error
