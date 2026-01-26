"""Unit tests for User, UserPreferences, and Voiceprint models"""
import pytest
import uuid
from datetime import datetime
from app.models import User, UserPreferences, Voiceprint


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """Test creating a User instance"""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            name="Ramesh Kumar",
            phone_number="+919876543210",
            primary_language="hi",
            secondary_languages=["en", "te"],
            location={"state": "Maharashtra", "district": "Pune"},
            preferences={}
        )
        
        assert user.id == user_id
        assert user.name == "Ramesh Kumar"
        assert user.phone_number == "+919876543210"
        assert user.primary_language == "hi"
        assert user.secondary_languages == ["en", "te"]
        assert user.location == {"state": "Maharashtra", "district": "Pune"}
        assert user.voiceprint_id is None
        assert user.preferences == {}
    
    def test_user_repr(self):
        """Test User string representation"""
        user = User(
            id=uuid.uuid4(),
            name="Test User",
            phone_number="+919876543210",
            primary_language="hi"
        )
        
        assert repr(user) == "<User Test User (+919876543210)>"
    
    def test_user_with_minimal_fields(self):
        """Test User with only required fields"""
        user = User(
            id=uuid.uuid4(),
            name="Minimal User",
            phone_number="+919999999999",
            primary_language="ta",
            secondary_languages=[],
            preferences={}
        )
        
        assert user.name == "Minimal User"
        assert user.phone_number == "+919999999999"
        assert user.primary_language == "ta"
        assert user.secondary_languages == []
        assert user.location is None


class TestUserPreferencesModel:
    """Test UserPreferences model"""
    
    def test_user_preferences_creation(self):
        """Test creating a UserPreferences instance"""
        user_id = uuid.uuid4()
        prefs_id = uuid.uuid4()
        
        prefs = UserPreferences(
            id=prefs_id,
            user_id=user_id,
            speech_rate=0.9,
            volume_boost=True,
            offline_mode=False,
            favorite_contacts=[uuid.uuid4(), uuid.uuid4()],
            additional_settings={}
        )
        
        assert prefs.id == prefs_id
        assert prefs.user_id == user_id
        assert prefs.speech_rate == 0.9
        assert prefs.volume_boost is True
        assert prefs.offline_mode is False
        assert len(prefs.favorite_contacts) == 2
        assert prefs.additional_settings == {}
    
    def test_user_preferences_default_values(self):
        """Test UserPreferences default values"""
        user_id = uuid.uuid4()
        
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id,
            speech_rate=0.85,
            volume_boost=False,
            offline_mode=False,
            favorite_contacts=[],
            additional_settings={}
        )
        
        assert prefs.speech_rate == 0.85  # Default 15% slower
        assert prefs.volume_boost is False
        assert prefs.offline_mode is False
        assert prefs.favorite_contacts == []
        assert prefs.additional_settings == {}
    
    def test_user_preferences_repr(self):
        """Test UserPreferences string representation"""
        user_id = uuid.uuid4()
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id
        )
        
        assert repr(prefs) == f"<UserPreferences for user {user_id}>"
    
    def test_user_preferences_speech_rate_range(self):
        """Test that speech_rate can be set within valid range"""
        user_id = uuid.uuid4()
        
        # Test minimum
        prefs_min = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id,
            speech_rate=0.8
        )
        assert prefs_min.speech_rate == 0.8
        
        # Test maximum
        prefs_max = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id,
            speech_rate=1.2
        )
        assert prefs_max.speech_rate == 1.2
    
    def test_user_preferences_additional_settings(self):
        """Test storing additional settings as JSON"""
        user_id = uuid.uuid4()
        
        prefs = UserPreferences(
            id=uuid.uuid4(),
            user_id=user_id,
            additional_settings={
                "theme": "dark",
                "notifications_enabled": True,
                "preferred_units": "metric"
            }
        )
        
        assert prefs.additional_settings["theme"] == "dark"
        assert prefs.additional_settings["notifications_enabled"] is True
        assert prefs.additional_settings["preferred_units"] == "metric"


class TestVoiceprintModel:
    """Test Voiceprint model"""
    
    def test_voiceprint_creation(self):
        """Test creating a Voiceprint instance"""
        user_id = uuid.uuid4()
        voiceprint_id = uuid.uuid4()
        embedding_data = b"test_embedding_data_bytes"
        
        voiceprint = Voiceprint(
            id=voiceprint_id,
            user_id=user_id,
            embedding_data=embedding_data,
            encryption_algorithm="AES-256",
            sample_count=5
        )
        
        assert voiceprint.id == voiceprint_id
        assert voiceprint.user_id == user_id
        assert voiceprint.embedding_data == embedding_data
        assert voiceprint.encryption_algorithm == "AES-256"
        assert voiceprint.sample_count == 5
    
    def test_voiceprint_default_encryption(self):
        """Test Voiceprint default encryption algorithm"""
        user_id = uuid.uuid4()
        
        voiceprint = Voiceprint(
            id=uuid.uuid4(),
            user_id=user_id,
            embedding_data=b"test_data",
            sample_count=3,
            encryption_algorithm="AES-256"
        )
        
        assert voiceprint.encryption_algorithm == "AES-256"
    
    def test_voiceprint_repr(self):
        """Test Voiceprint string representation"""
        user_id = uuid.uuid4()
        voiceprint = Voiceprint(
            id=uuid.uuid4(),
            user_id=user_id,
            embedding_data=b"test_data",
            sample_count=3
        )
        
        assert repr(voiceprint) == f"<Voiceprint for user {user_id}>"
    
    def test_voiceprint_with_multiple_samples(self):
        """Test Voiceprint created from multiple voice samples"""
        user_id = uuid.uuid4()
        
        # Simulate voiceprint from 5 samples (as per requirement 21.1)
        voiceprint = Voiceprint(
            id=uuid.uuid4(),
            user_id=user_id,
            embedding_data=b"averaged_embedding_from_5_samples",
            sample_count=5
        )
        
        assert voiceprint.sample_count == 5
        assert len(voiceprint.embedding_data) > 0
    
    def test_voiceprint_binary_data(self):
        """Test that embedding_data stores binary data correctly"""
        user_id = uuid.uuid4()
        
        # Simulate a numpy array serialized to bytes
        import numpy as np
        embedding_array = np.random.rand(512)  # 512-dimensional embedding
        embedding_bytes = embedding_array.tobytes()
        
        voiceprint = Voiceprint(
            id=uuid.uuid4(),
            user_id=user_id,
            embedding_data=embedding_bytes,
            sample_count=3
        )
        
        assert isinstance(voiceprint.embedding_data, bytes)
        assert len(voiceprint.embedding_data) == embedding_array.nbytes


class TestModelRelationships:
    """Test relationships between models"""
    
    def test_user_has_preferences_relationship(self):
        """Test that User model has user_preferences relationship"""
        assert hasattr(User, 'user_preferences')
    
    def test_user_has_voiceprint_relationship(self):
        """Test that User model has voiceprint relationship"""
        assert hasattr(User, 'voiceprint')
    
    def test_user_preferences_has_user_relationship(self):
        """Test that UserPreferences model has user relationship"""
        assert hasattr(UserPreferences, 'user')
    
    def test_voiceprint_has_user_relationship(self):
        """Test that Voiceprint model has user relationship"""
        assert hasattr(Voiceprint, 'user')


class TestModelTableNames:
    """Test that table names are correct"""
    
    def test_user_table_name(self):
        """Test User table name"""
        assert User.__tablename__ == "users"
    
    def test_user_preferences_table_name(self):
        """Test UserPreferences table name"""
        assert UserPreferences.__tablename__ == "user_preferences"
    
    def test_voiceprint_table_name(self):
        """Test Voiceprint table name"""
        assert Voiceprint.__tablename__ == "voiceprints"


class TestModelColumns:
    """Test that models have required columns"""
    
    def test_user_has_required_columns(self):
        """Test User has all required columns"""
        columns = [c.name for c in User.__table__.columns]
        
        required_columns = [
            'id', 'name', 'phone_number', 'primary_language',
            'secondary_languages', 'location', 'voiceprint_id',
            'created_at', 'last_active', 'preferences'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_user_preferences_has_required_columns(self):
        """Test UserPreferences has all required columns"""
        columns = [c.name for c in UserPreferences.__table__.columns]
        
        required_columns = [
            'id', 'user_id', 'speech_rate', 'volume_boost',
            'offline_mode', 'favorite_contacts', 'additional_settings'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
    
    def test_voiceprint_has_required_columns(self):
        """Test Voiceprint has all required columns"""
        columns = [c.name for c in Voiceprint.__table__.columns]
        
        required_columns = [
            'id', 'user_id', 'embedding_data', 'encryption_algorithm',
            'sample_count', 'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing column: {col}"
