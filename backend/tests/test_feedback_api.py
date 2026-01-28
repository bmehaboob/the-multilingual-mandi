"""
Unit tests for feedback collection API endpoints.

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
import pytest
from datetime import datetime
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.main import app
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.feedback import (
    TranscriptionFeedback,
    NegotiationFeedback,
    SatisfactionSurvey,
    TranslationFeedback,
    PriceOracleFeedback,
    SatisfactionRating
)


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user():
    """Override current user dependency for testing"""
    return User(
        id=uuid4(),
        phone_number="+919876543210",
        name="Test User",
        primary_language="hi",
        location_state="Maharashtra",
        location_district="Mumbai"
    )


# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestTranscriptionCorrectionEndpoint:
    """Tests for transcription correction endpoint"""
    
    def test_submit_transcription_correction_success(self):
        """Test successful submission of transcription correction"""
        correction_data = {
            "incorrect_transcription": "टमाटर का भाव क्या है",
            "correct_transcription": "टमाटर का भाव क्या है",
            "language": "hi",
            "confidence_score": 0.65
        }
        
        response = client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["incorrect_transcription"] == correction_data["incorrect_transcription"]
        assert data["correct_transcription"] == correction_data["correct_transcription"]
        assert data["language"] == correction_data["language"]
        assert data["confidence_score"] == correction_data["confidence_score"]
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
    
    def test_submit_transcription_correction_with_metadata(self):
        """Test submission with metadata"""
        correction_data = {
            "incorrect_transcription": "wrong text",
            "correct_transcription": "correct text",
            "language": "en",
            "dialect": "Indian English",
            "metadata": {
                "noise_level": "high",
                "environment": "market"
            }
        }
        
        response = client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["dialect"] == "Indian English"
        assert data["metadata"]["noise_level"] == "high"
    
    def test_submit_transcription_correction_missing_required_fields(self):
        """Test submission with missing required fields"""
        correction_data = {
            "incorrect_transcription": "wrong text"
            # Missing correct_transcription and language
        }
        
        response = client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        assert response.status_code == 422  # Validation error


class TestNegotiationFeedbackEndpoint:
    """Tests for negotiation feedback endpoint"""
    
    def test_submit_negotiation_feedback_success(self):
        """Test successful submission of negotiation feedback"""
        feedback_data = {
            "rating": 5,
            "was_helpful": True,
            "was_culturally_appropriate": True,
            "was_used": True,
            "commodity": "tomato",
            "suggested_price": 25.0,
            "market_average": 23.0,
            "language": "hi",
            "region": "Maharashtra"
        }
        
        response = client.post("/api/v1/feedback/negotiation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["was_helpful"] is True
        assert data["was_culturally_appropriate"] is True
        assert data["commodity"] == "tomato"
        assert data["suggested_price"] == 25.0
    
    def test_submit_negotiation_feedback_with_text(self):
        """Test submission with free-form feedback text"""
        feedback_data = {
            "rating": 4,
            "was_helpful": True,
            "feedback_text": "The suggestion was good but could be more polite",
            "commodity": "onion"
        }
        
        response = client.post("/api/v1/feedback/negotiation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["feedback_text"] == "The suggestion was good but could be more polite"
    
    def test_submit_negotiation_feedback_invalid_rating(self):
        """Test submission with invalid rating (out of range)"""
        feedback_data = {
            "rating": 6,  # Invalid: should be 1-5
            "was_helpful": True
        }
        
        response = client.post("/api/v1/feedback/negotiation", json=feedback_data)
        
        assert response.status_code == 422  # Validation error


class TestSatisfactionSurveyEndpoint:
    """Tests for satisfaction survey endpoint"""
    
    def test_submit_satisfaction_survey_success(self):
        """Test successful submission of satisfaction survey"""
        survey_data = {
            "survey_type": "post_transaction",
            "overall_rating": "satisfied",
            "voice_translation_rating": 5,
            "price_oracle_rating": 4,
            "negotiation_assistant_rating": 5,
            "price_oracle_helpful": True,
            "negotiation_suggestions_helpful": True,
            "language": "hi"
        }
        
        response = client.post("/api/v1/feedback/satisfaction-survey", json=survey_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["survey_type"] == "post_transaction"
        assert data["overall_rating"] == "satisfied"
        assert data["voice_translation_rating"] == 5
        assert data["price_oracle_helpful"] is True
    
    def test_submit_satisfaction_survey_with_transaction_id(self):
        """Test submission linked to a transaction"""
        transaction_id = str(uuid4())
        survey_data = {
            "survey_type": "post_transaction",
            "transaction_id": transaction_id,
            "overall_rating": "very_satisfied",
            "language": "te"
        }
        
        response = client.post("/api/v1/feedback/satisfaction-survey", json=survey_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_id"] == transaction_id
    
    def test_submit_satisfaction_survey_minimal_data(self):
        """Test submission with only required fields"""
        survey_data = {
            "survey_type": "periodic",
            "overall_rating": "neutral",
            "language": "en"
        }
        
        response = client.post("/api/v1/feedback/satisfaction-survey", json=survey_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["overall_rating"] == "neutral"


class TestTranslationFeedbackEndpoint:
    """Tests for translation feedback endpoint"""
    
    def test_submit_translation_feedback_success(self):
        """Test successful submission of translation feedback"""
        feedback_data = {
            "source_text": "टमाटर का भाव क्या है",
            "translated_text": "What is the price of tomatoes",
            "source_language": "hi",
            "target_language": "en",
            "rating": 5,
            "was_accurate": True,
            "preserved_meaning": True
        }
        
        response = client.post("/api/v1/feedback/translation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["source_text"] == feedback_data["source_text"]
        assert data["translated_text"] == feedback_data["translated_text"]
        assert data["rating"] == 5
        assert data["was_accurate"] is True
    
    def test_submit_translation_feedback_with_correction(self):
        """Test submission with corrected translation"""
        feedback_data = {
            "source_text": "मुझे प्याज चाहिए",
            "translated_text": "I want onions",
            "source_language": "hi",
            "target_language": "en",
            "rating": 3,
            "was_accurate": False,
            "corrected_translation": "I need onions",
            "feedback_text": "The translation is too casual"
        }
        
        response = client.post("/api/v1/feedback/translation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["corrected_translation"] == "I need onions"
        assert data["was_accurate"] is False


class TestPriceOracleFeedbackEndpoint:
    """Tests for price oracle feedback endpoint"""
    
    def test_submit_price_oracle_feedback_success(self):
        """Test successful submission of price oracle feedback"""
        feedback_data = {
            "commodity": "tomato",
            "quoted_price": 30.0,
            "market_average": 25.0,
            "price_verdict": "high",
            "was_helpful": True,
            "was_accurate": True,
            "influenced_decision": True,
            "rating": 5
        }
        
        response = client.post("/api/v1/feedback/price-oracle", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["commodity"] == "tomato"
        assert data["quoted_price"] == 30.0
        assert data["market_average"] == 25.0
        assert data["was_helpful"] is True
    
    def test_submit_price_oracle_feedback_not_helpful(self):
        """Test submission when price oracle was not helpful"""
        feedback_data = {
            "commodity": "onion",
            "was_helpful": False,
            "was_accurate": False,
            "feedback_text": "The price data seemed outdated"
        }
        
        response = client.post("/api/v1/feedback/price-oracle", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["was_helpful"] is False
        assert data["feedback_text"] == "The price data seemed outdated"


class TestVoiceSurveyInitiation:
    """Tests for voice survey initiation endpoint"""
    
    def test_initiate_post_transaction_survey(self):
        """Test initiating a post-transaction survey"""
        request_data = {
            "survey_type": "post_transaction",
            "language": "hi"
        }
        
        response = client.post("/api/v1/feedback/voice-survey/initiate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "prompt_text" in data
        assert "expected_response_type" in data
        assert data["expected_response_type"] in ["rating", "boolean", "text"]
    
    def test_initiate_periodic_survey(self):
        """Test initiating a periodic survey"""
        request_data = {
            "survey_type": "periodic",
            "language": "te"
        }
        
        response = client.post("/api/v1/feedback/voice-survey/initiate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "prompt_text" in data


class TestFeedbackRetrieval:
    """Tests for retrieving user's feedback submissions"""
    
    def test_get_transcription_corrections(self):
        """Test retrieving user's transcription corrections"""
        # First submit some corrections
        for i in range(3):
            correction_data = {
                "incorrect_transcription": f"wrong text {i}",
                "correct_transcription": f"correct text {i}",
                "language": "hi"
            }
            client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        # Retrieve corrections
        response = client.get("/api/v1/feedback/transcription-corrections")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
    
    def test_get_negotiation_feedback(self):
        """Test retrieving user's negotiation feedback"""
        # Submit feedback
        feedback_data = {
            "rating": 4,
            "was_helpful": True
        }
        client.post("/api/v1/feedback/negotiation", json=feedback_data)
        
        # Retrieve feedback
        response = client.get("/api/v1/feedback/negotiation-feedback")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
    
    def test_get_satisfaction_surveys(self):
        """Test retrieving user's satisfaction surveys"""
        # Submit survey
        survey_data = {
            "survey_type": "periodic",
            "overall_rating": "satisfied",
            "language": "hi"
        }
        client.post("/api/v1/feedback/satisfaction-survey", json=survey_data)
        
        # Retrieve surveys
        response = client.get("/api/v1/feedback/satisfaction-surveys")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
    
    def test_get_feedback_with_pagination(self):
        """Test retrieving feedback with pagination"""
        # Submit multiple corrections
        for i in range(15):
            correction_data = {
                "incorrect_transcription": f"wrong {i}",
                "correct_transcription": f"correct {i}",
                "language": "hi"
            }
            client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        # Get first page
        response = client.get("/api/v1/feedback/transcription-corrections?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Get second page
        response = client.get("/api/v1/feedback/transcription-corrections?limit=10&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


class TestFeedbackDataIntegrity:
    """Tests for data integrity and validation"""
    
    def test_transcription_correction_stores_all_fields(self):
        """Test that all fields are properly stored"""
        correction_data = {
            "message_id": str(uuid4()),
            "audio_hash": "abc123def456",
            "incorrect_transcription": "wrong",
            "correct_transcription": "correct",
            "language": "hi",
            "confidence_score": 0.75,
            "dialect": "Marathi-influenced Hindi",
            "metadata": {"key": "value"}
        }
        
        response = client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message_id"] == correction_data["message_id"]
        assert data["audio_hash"] == correction_data["audio_hash"]
        assert data["dialect"] == correction_data["dialect"]
        assert data["metadata"] == correction_data["metadata"]
    
    def test_negotiation_feedback_stores_all_fields(self):
        """Test that all negotiation feedback fields are stored"""
        conversation_id = str(uuid4())
        feedback_data = {
            "conversation_id": conversation_id,
            "suggestion_id": "sug_123",
            "suggested_price": 25.0,
            "suggested_message": "भाई साहब, 25 रुपये में दे दीजिए",
            "rating": 5,
            "was_helpful": True,
            "was_culturally_appropriate": True,
            "was_used": True,
            "feedback_text": "Very helpful suggestion",
            "commodity": "tomato",
            "market_average": 23.0,
            "language": "hi",
            "region": "Maharashtra",
            "metadata": {"session": "abc"}
        }
        
        response = client.post("/api/v1/feedback/negotiation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert data["suggestion_id"] == "sug_123"
        assert data["suggested_message"] == feedback_data["suggested_message"]
        assert data["metadata"] == feedback_data["metadata"]
    
    def test_satisfaction_survey_stores_all_ratings(self):
        """Test that all rating fields are stored"""
        survey_data = {
            "survey_type": "post_transaction",
            "overall_rating": "very_satisfied",
            "voice_translation_rating": 5,
            "price_oracle_rating": 4,
            "negotiation_assistant_rating": 5,
            "price_oracle_helpful": True,
            "negotiation_suggestions_helpful": True,
            "negotiation_culturally_appropriate": True,
            "feedback_text": "Excellent experience",
            "language": "hi"
        }
        
        response = client.post("/api/v1/feedback/satisfaction-survey", json=survey_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["voice_translation_rating"] == 5
        assert data["price_oracle_rating"] == 4
        assert data["negotiation_assistant_rating"] == 5
        assert data["price_oracle_helpful"] is True
        assert data["negotiation_suggestions_helpful"] is True
        assert data["negotiation_culturally_appropriate"] is True


class TestFeedbackRequirementsCoverage:
    """Tests to verify requirements coverage"""
    
    def test_requirement_20_1_transcription_correction_logging(self):
        """
        Requirement 20.1: When a user corrects a transcription error,
        the platform shall log the original audio, incorrect transcription,
        and user correction.
        """
        correction_data = {
            "audio_hash": "hash_of_audio_file",
            "incorrect_transcription": "wrong transcription",
            "correct_transcription": "correct transcription",
            "language": "hi"
        }
        
        response = client.post("/api/v1/feedback/transcription-correction", json=correction_data)
        
        assert response.status_code == 201
        data = response.json()
        # Verify all required data is logged
        assert data["audio_hash"] is not None
        assert data["incorrect_transcription"] is not None
        assert data["correct_transcription"] is not None
        assert data["language"] is not None
    
    def test_requirement_20_2_translation_quality_feedback(self):
        """
        Requirement 20.2: The platform shall collect user feedback on
        translation quality through simple voice-based ratings.
        """
        feedback_data = {
            "source_text": "test",
            "translated_text": "परीक्षण",
            "source_language": "en",
            "target_language": "hi",
            "rating": 4,
            "was_accurate": True
        }
        
        response = client.post("/api/v1/feedback/translation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] >= 1 and data["rating"] <= 5
    
    def test_requirement_22_1_periodic_satisfaction_surveys(self):
        """
        Requirement 22.1: The platform shall conduct periodic voice-based
        satisfaction surveys asking users to rate their experience.
        """
        survey_data = {
            "survey_type": "periodic",
            "overall_rating": "satisfied",
            "language": "hi"
        }
        
        response = client.post("/api/v1/feedback/satisfaction-survey", json=survey_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["survey_type"] == "periodic"
        assert data["overall_rating"] in ["very_dissatisfied", "dissatisfied", "neutral", "satisfied", "very_satisfied"]
    
    def test_requirement_22_3_price_oracle_helpfulness(self):
        """
        Requirement 22.3: When a transaction is completed, the platform
        shall ask users if they found the Fair Price Oracle helpful.
        """
        feedback_data = {
            "commodity": "tomato",
            "was_helpful": True,
            "influenced_decision": True
        }
        
        response = client.post("/api/v1/feedback/price-oracle", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "was_helpful" in data
        assert isinstance(data["was_helpful"], bool)
    
    def test_requirement_22_4_negotiation_suggestions_feedback(self):
        """
        Requirement 22.4: When a negotiation concludes, the platform shall
        ask users if the Sauda Bot suggestions were culturally appropriate
        and useful.
        """
        feedback_data = {
            "rating": 5,
            "was_helpful": True,
            "was_culturally_appropriate": True,
            "was_used": True
        }
        
        response = client.post("/api/v1/feedback/negotiation", json=feedback_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "was_helpful" in data
        assert "was_culturally_appropriate" in data
        assert isinstance(data["was_helpful"], bool)
        assert isinstance(data["was_culturally_appropriate"], bool)
