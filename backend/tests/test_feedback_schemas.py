"""
Unit tests for feedback schemas (no database required).

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
import pytest
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.feedback import (
    TranscriptionCorrectionCreate,
    NegotiationFeedbackCreate,
    SatisfactionSurveyCreate,
    TranslationFeedbackCreate,
    PriceOracleFeedbackCreate,
    VoiceSurveyRequest
)
from app.models.feedback import SatisfactionRating


class TestTranscriptionCorrectionSchema:
    """Tests for transcription correction schema validation"""
    
    def test_valid_transcription_correction(self):
        """Test creating a valid transcription correction"""
        data = {
            "incorrect_transcription": "wrong text",
            "correct_transcription": "correct text",
            "language": "hi"
        }
        correction = TranscriptionCorrectionCreate(**data)
        assert correction.incorrect_transcription == "wrong text"
        assert correction.correct_transcription == "correct text"
        assert correction.language == "hi"
    
    def test_transcription_correction_with_optional_fields(self):
        """Test transcription correction with all optional fields"""
        data = {
            "message_id": uuid4(),
            "audio_hash": "abc123",
            "incorrect_transcription": "wrong",
            "correct_transcription": "correct",
            "language": "hi",
            "confidence_score": 0.75,
            "dialect": "Marathi-influenced Hindi",
            "metadata": {"key": "value"}
        }
        correction = TranscriptionCorrectionCreate(**data)
        assert correction.confidence_score == 0.75
        assert correction.dialect == "Marathi-influenced Hindi"
    
    def test_transcription_correction_missing_required_field(self):
        """Test that missing required fields raise validation error"""
        data = {
            "incorrect_transcription": "wrong"
            # Missing correct_transcription and language
        }
        with pytest.raises(ValidationError):
            TranscriptionCorrectionCreate(**data)
    
    def test_transcription_correction_empty_text(self):
        """Test that empty transcription text is rejected"""
        data = {
            "incorrect_transcription": "",
            "correct_transcription": "correct",
            "language": "hi"
        }
        with pytest.raises(ValidationError):
            TranscriptionCorrectionCreate(**data)
    
    def test_transcription_correction_invalid_confidence_score(self):
        """Test that confidence score must be between 0 and 1"""
        data = {
            "incorrect_transcription": "wrong",
            "correct_transcription": "correct",
            "language": "hi",
            "confidence_score": 1.5  # Invalid: > 1.0
        }
        with pytest.raises(ValidationError):
            TranscriptionCorrectionCreate(**data)


class TestNegotiationFeedbackSchema:
    """Tests for negotiation feedback schema validation"""
    
    def test_valid_negotiation_feedback(self):
        """Test creating valid negotiation feedback"""
        data = {
            "rating": 5,
            "was_helpful": True
        }
        feedback = NegotiationFeedbackCreate(**data)
        assert feedback.rating == 5
        assert feedback.was_helpful is True
    
    def test_negotiation_feedback_with_all_fields(self):
        """Test negotiation feedback with all fields"""
        data = {
            "conversation_id": uuid4(),
            "suggestion_id": "sug_123",
            "suggested_price": 25.0,
            "suggested_message": "भाई साहब, 25 रुपये में दे दीजिए",
            "rating": 5,
            "was_helpful": True,
            "was_culturally_appropriate": True,
            "was_used": True,
            "feedback_text": "Very helpful",
            "commodity": "tomato",
            "market_average": 23.0,
            "language": "hi",
            "region": "Maharashtra",
            "metadata": {"session": "abc"}
        }
        feedback = NegotiationFeedbackCreate(**data)
        assert feedback.suggested_price == 25.0
        assert feedback.was_culturally_appropriate is True
    
    def test_negotiation_feedback_invalid_rating(self):
        """Test that rating must be between 1 and 5"""
        data = {
            "rating": 6,  # Invalid: > 5
            "was_helpful": True
        }
        with pytest.raises(ValidationError):
            NegotiationFeedbackCreate(**data)
        
        data["rating"] = 0  # Invalid: < 1
        with pytest.raises(ValidationError):
            NegotiationFeedbackCreate(**data)
    
    def test_negotiation_feedback_negative_price(self):
        """Test that prices must be positive"""
        data = {
            "rating": 5,
            "was_helpful": True,
            "suggested_price": -10.0  # Invalid: negative
        }
        with pytest.raises(ValidationError):
            NegotiationFeedbackCreate(**data)


class TestSatisfactionSurveySchema:
    """Tests for satisfaction survey schema validation"""
    
    def test_valid_satisfaction_survey(self):
        """Test creating a valid satisfaction survey"""
        data = {
            "survey_type": "post_transaction",
            "overall_rating": "satisfied",
            "language": "hi"
        }
        survey = SatisfactionSurveyCreate(**data)
        assert survey.survey_type == "post_transaction"
        assert survey.overall_rating == SatisfactionRating.SATISFIED
        assert survey.language == "hi"
    
    def test_satisfaction_survey_with_all_ratings(self):
        """Test survey with all rating fields"""
        data = {
            "survey_type": "periodic",
            "overall_rating": "very_satisfied",
            "voice_translation_rating": 5,
            "price_oracle_rating": 4,
            "negotiation_assistant_rating": 5,
            "price_oracle_helpful": True,
            "negotiation_suggestions_helpful": True,
            "negotiation_culturally_appropriate": True,
            "language": "te"
        }
        survey = SatisfactionSurveyCreate(**data)
        assert survey.voice_translation_rating == 5
        assert survey.price_oracle_rating == 4
        assert survey.negotiation_assistant_rating == 5
    
    def test_satisfaction_survey_invalid_feature_rating(self):
        """Test that feature ratings must be between 1 and 5"""
        data = {
            "survey_type": "periodic",
            "overall_rating": "satisfied",
            "voice_translation_rating": 6,  # Invalid: > 5
            "language": "hi"
        }
        with pytest.raises(ValidationError):
            SatisfactionSurveyCreate(**data)
    
    def test_satisfaction_survey_all_rating_levels(self):
        """Test all satisfaction rating levels"""
        rating_levels = [
            "very_dissatisfied",
            "dissatisfied",
            "neutral",
            "satisfied",
            "very_satisfied"
        ]
        
        for rating in rating_levels:
            data = {
                "survey_type": "periodic",
                "overall_rating": rating,
                "language": "hi"
            }
            survey = SatisfactionSurveyCreate(**data)
            assert survey.overall_rating.value == rating


class TestTranslationFeedbackSchema:
    """Tests for translation feedback schema validation"""
    
    def test_valid_translation_feedback(self):
        """Test creating valid translation feedback"""
        data = {
            "source_text": "टमाटर का भाव क्या है",
            "translated_text": "What is the price of tomatoes",
            "source_language": "hi",
            "target_language": "en",
            "rating": 5,
            "was_accurate": True
        }
        feedback = TranslationFeedbackCreate(**data)
        assert feedback.source_text == "टमाटर का भाव क्या है"
        assert feedback.rating == 5
        assert feedback.was_accurate is True
    
    def test_translation_feedback_with_correction(self):
        """Test translation feedback with corrected translation"""
        data = {
            "source_text": "मुझे प्याज चाहिए",
            "translated_text": "I want onions",
            "source_language": "hi",
            "target_language": "en",
            "rating": 3,
            "was_accurate": False,
            "corrected_translation": "I need onions",
            "feedback_text": "Translation is too casual"
        }
        feedback = TranslationFeedbackCreate(**data)
        assert feedback.corrected_translation == "I need onions"
        assert feedback.was_accurate is False
    
    def test_translation_feedback_empty_text(self):
        """Test that empty text is rejected"""
        data = {
            "source_text": "",
            "translated_text": "text",
            "source_language": "hi",
            "target_language": "en",
            "rating": 5,
            "was_accurate": True
        }
        with pytest.raises(ValidationError):
            TranslationFeedbackCreate(**data)


class TestPriceOracleFeedbackSchema:
    """Tests for price oracle feedback schema validation"""
    
    def test_valid_price_oracle_feedback(self):
        """Test creating valid price oracle feedback"""
        data = {
            "commodity": "tomato",
            "was_helpful": True
        }
        feedback = PriceOracleFeedbackCreate(**data)
        assert feedback.commodity == "tomato"
        assert feedback.was_helpful is True
    
    def test_price_oracle_feedback_with_all_fields(self):
        """Test price oracle feedback with all fields"""
        data = {
            "transaction_id": uuid4(),
            "conversation_id": uuid4(),
            "commodity": "tomato",
            "quoted_price": 30.0,
            "market_average": 25.0,
            "price_verdict": "high",
            "was_helpful": True,
            "was_accurate": True,
            "influenced_decision": True,
            "rating": 5,
            "feedback_text": "Very helpful",
            "metadata": {"source": "enam"}
        }
        feedback = PriceOracleFeedbackCreate(**data)
        assert feedback.quoted_price == 30.0
        assert feedback.market_average == 25.0
        assert feedback.price_verdict == "high"
    
    def test_price_oracle_feedback_negative_price(self):
        """Test that prices must be positive"""
        data = {
            "commodity": "tomato",
            "quoted_price": -10.0,  # Invalid: negative
            "was_helpful": True
        }
        with pytest.raises(ValidationError):
            PriceOracleFeedbackCreate(**data)
    
    def test_price_oracle_feedback_empty_commodity(self):
        """Test that commodity name cannot be empty"""
        data = {
            "commodity": "",
            "was_helpful": True
        }
        with pytest.raises(ValidationError):
            PriceOracleFeedbackCreate(**data)


class TestVoiceSurveyRequestSchema:
    """Tests for voice survey request schema validation"""
    
    def test_valid_voice_survey_request(self):
        """Test creating a valid voice survey request"""
        data = {
            "survey_type": "post_transaction",
            "language": "hi"
        }
        request = VoiceSurveyRequest(**data)
        assert request.survey_type == "post_transaction"
        assert request.language == "hi"
    
    def test_voice_survey_request_with_context(self):
        """Test voice survey request with transaction/conversation context"""
        data = {
            "survey_type": "post_transaction",
            "language": "te",
            "transaction_id": uuid4(),
            "conversation_id": uuid4()
        }
        request = VoiceSurveyRequest(**data)
        assert request.transaction_id is not None
        assert request.conversation_id is not None


class TestSchemaRequirementsCoverage:
    """Tests to verify that schemas support all requirements"""
    
    def test_requirement_20_1_transcription_correction_fields(self):
        """
        Requirement 20.1: Schema must support logging original audio,
        incorrect transcription, and user correction.
        """
        data = {
            "audio_hash": "hash123",
            "incorrect_transcription": "wrong",
            "correct_transcription": "correct",
            "language": "hi"
        }
        correction = TranscriptionCorrectionCreate(**data)
        # Verify all required fields are present
        assert hasattr(correction, 'audio_hash')
        assert hasattr(correction, 'incorrect_transcription')
        assert hasattr(correction, 'correct_transcription')
        assert hasattr(correction, 'language')
    
    def test_requirement_20_2_translation_quality_rating(self):
        """
        Requirement 20.2: Schema must support voice-based ratings
        for translation quality.
        """
        data = {
            "source_text": "test",
            "translated_text": "परीक्षण",
            "source_language": "en",
            "target_language": "hi",
            "rating": 4,
            "was_accurate": True
        }
        feedback = TranslationFeedbackCreate(**data)
        assert hasattr(feedback, 'rating')
        assert feedback.rating >= 1 and feedback.rating <= 5
    
    def test_requirement_22_1_periodic_satisfaction_surveys(self):
        """
        Requirement 22.1: Schema must support periodic satisfaction surveys.
        """
        data = {
            "survey_type": "periodic",
            "overall_rating": "satisfied",
            "language": "hi"
        }
        survey = SatisfactionSurveyCreate(**data)
        assert survey.survey_type == "periodic"
        assert hasattr(survey, 'overall_rating')
    
    def test_requirement_22_3_price_oracle_helpfulness_field(self):
        """
        Requirement 22.3: Schema must support asking if Price Oracle
        was helpful.
        """
        data = {
            "commodity": "tomato",
            "was_helpful": True
        }
        feedback = PriceOracleFeedbackCreate(**data)
        assert hasattr(feedback, 'was_helpful')
        assert isinstance(feedback.was_helpful, bool)
    
    def test_requirement_22_4_negotiation_cultural_appropriateness(self):
        """
        Requirement 22.4: Schema must support feedback on cultural
        appropriateness of negotiation suggestions.
        """
        data = {
            "rating": 5,
            "was_helpful": True,
            "was_culturally_appropriate": True
        }
        feedback = NegotiationFeedbackCreate(**data)
        assert hasattr(feedback, 'was_helpful')
        assert hasattr(feedback, 'was_culturally_appropriate')
        assert isinstance(feedback.was_culturally_appropriate, bool)
    
    def test_all_feedback_types_support_metadata(self):
        """Test that all feedback types support metadata for extensibility"""
        # Transcription correction
        tc = TranscriptionCorrectionCreate(
            incorrect_transcription="wrong",
            correct_transcription="correct",
            language="hi",
            metadata={"key": "value"}
        )
        assert tc.event_metadata == {"key": "value"}
        
        # Negotiation feedback
        nf = NegotiationFeedbackCreate(
            rating=5,
            was_helpful=True,
            metadata={"key": "value"}
        )
        assert nf.event_metadata == {"key": "value"}
        
        # Satisfaction survey
        ss = SatisfactionSurveyCreate(
            survey_type="periodic",
            overall_rating="satisfied",
            language="hi",
            metadata={"key": "value"}
        )
        assert ss.event_metadata == {"key": "value"}
        
        # Translation feedback
        tf = TranslationFeedbackCreate(
            source_text="test",
            translated_text="परीक्षण",
            source_language="en",
            target_language="hi",
            rating=5,
            was_accurate=True,
            metadata={"key": "value"}
        )
        assert tf.event_metadata == {"key": "value"}
        
        # Price oracle feedback
        pf = PriceOracleFeedbackCreate(
            commodity="tomato",
            was_helpful=True,
            metadata={"key": "value"}
        )
        assert pf.event_metadata == {"key": "value"}
