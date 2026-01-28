"""Unit tests for ErrorHandler service

Tests error categorization, multilingual messages, and corrective actions.
Requirements: 14.1, 14.2
"""
import pytest
from datetime import datetime
from app.services.error_handler import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorResponse,
    CorrectiveAction,
)


@pytest.fixture
def error_handler():
    """Create ErrorHandler instance"""
    return ErrorHandler()


@pytest.fixture
def base_context():
    """Create base error context"""
    return ErrorContext(
        user_id="test_user_123",
        user_language="en",
        conversation_id="conv_456",
        operation="test_operation",
        timestamp=datetime.now()
    )


class TestErrorCategorization:
    """Test error categorization logic"""
    
    def test_categorize_network_error_by_type(self, error_handler):
        """Test network error categorization by exception type"""
        error = ConnectionError("Connection timeout")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.NETWORK
    
    def test_categorize_network_error_by_message(self, error_handler):
        """Test network error categorization by error message"""
        error = Exception("Network connection failed")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.NETWORK
    
    def test_categorize_audio_error(self, error_handler):
        """Test audio error categorization"""
        error = Exception("Audio quality too poor")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.AUDIO
    
    def test_categorize_translation_error(self, error_handler):
        """Test translation error categorization"""
        error = Exception("Translation confidence too low")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.TRANSLATION
    
    def test_categorize_service_error(self, error_handler):
        """Test service error categorization"""
        error = Exception("Service unavailable")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.SERVICE
    
    def test_categorize_data_error(self, error_handler):
        """Test data error categorization"""
        error = Exception("Data not found")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.DATA
    
    def test_categorize_authentication_error(self, error_handler):
        """Test authentication error categorization"""
        error = Exception("Unauthorized access")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.AUTHENTICATION
    
    def test_categorize_validation_error(self, error_handler):
        """Test validation error categorization"""
        error = Exception("Invalid input provided")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.VALIDATION
    
    def test_categorize_unknown_error(self, error_handler):
        """Test unknown error categorization"""
        error = Exception("Something went wrong")
        category = error_handler._categorize_error(error)
        assert category == ErrorCategory.UNKNOWN


class TestNetworkErrorHandling:
    """Test network error handling"""
    
    def test_network_error_response_structure(self, error_handler, base_context):
        """Test network error response has correct structure"""
        error = ConnectionError("Connection timeout")
        response = error_handler._handle_network_error(error, base_context)
        
        assert isinstance(response, ErrorResponse)
        assert response.category == ErrorCategory.NETWORK
        assert response.severity == ErrorSeverity.MEDIUM
        assert response.should_retry is True
        assert response.can_continue is True
        assert response.error_code == "NET_001"
    
    def test_network_error_corrective_actions(self, error_handler, base_context):
        """Test network error provides corrective actions"""
        error = ConnectionError("Connection timeout")
        response = error_handler._handle_network_error(error, base_context)
        
        assert len(response.corrective_actions) >= 2
        action_ids = [action.action_id for action in response.corrective_actions]
        assert "check_connection" in action_ids
        assert "switch_offline" in action_ids
    
    def test_network_error_automatic_actions(self, error_handler, base_context):
        """Test network error includes automatic actions"""
        error = ConnectionError("Connection timeout")
        response = error_handler._handle_network_error(error, base_context)
        
        automatic_actions = [a for a in response.corrective_actions if a.is_automatic]
        assert len(automatic_actions) > 0



class TestAudioErrorHandling:
    """Test audio error handling"""
    
    def test_audio_noise_error(self, error_handler, base_context):
        """Test audio noise error handling"""
        error = Exception("Audio quality poor due to noise")
        response = error_handler._handle_audio_error(error, base_context)
        
        assert response.category == ErrorCategory.AUDIO
        assert response.severity == ErrorSeverity.MEDIUM
        assert "noise" in response.message.lower() or "quiet" in response.message.lower()
        
        action_ids = [action.action_id for action in response.corrective_actions]
        assert "reduce_noise" in action_ids or "speak_closer" in action_ids
    
    def test_audio_no_speech_error(self, error_handler, base_context):
        """Test no speech detected error handling"""
        error = Exception("No speech detected in audio")
        response = error_handler._handle_audio_error(error, base_context)
        
        assert response.category == ErrorCategory.AUDIO
        action_ids = [action.action_id for action in response.corrective_actions]
        assert "check_microphone" in action_ids or "speak_louder" in action_ids
    
    def test_audio_generic_error(self, error_handler, base_context):
        """Test generic audio error handling"""
        error = Exception("Audio processing failed")
        response = error_handler._handle_audio_error(error, base_context)
        
        assert response.category == ErrorCategory.AUDIO
        assert len(response.corrective_actions) >= 1
        assert response.should_retry is True


class TestTranslationErrorHandling:
    """Test translation error handling"""
    
    def test_translation_low_confidence_error(self, error_handler, base_context):
        """Test low confidence translation error"""
        error = Exception("Translation confidence below threshold")
        response = error_handler._handle_translation_error(error, base_context)
        
        assert response.category == ErrorCategory.TRANSLATION
        action_ids = [action.action_id for action in response.corrective_actions]
        assert "confirm_message" in action_ids or "speak_again" in action_ids
    
    def test_translation_generic_error(self, error_handler, base_context):
        """Test generic translation error"""
        error = Exception("Translation failed")
        response = error_handler._handle_translation_error(error, base_context)
        
        assert response.category == ErrorCategory.TRANSLATION
        assert response.should_retry is True


class TestServiceErrorHandling:
    """Test service error handling"""
    
    def test_service_unavailable_error(self, error_handler, base_context):
        """Test service unavailable error handling"""
        error = Exception("Service unavailable")
        response = error_handler._handle_service_error(error, base_context)
        
        assert response.category == ErrorCategory.SERVICE
        assert response.severity == ErrorSeverity.HIGH
        assert response.should_retry is True
        assert response.retry_after_seconds is not None
    
    def test_service_error_automatic_retry(self, error_handler, base_context):
        """Test service error includes automatic retry action"""
        error = Exception("Service unavailable")
        response = error_handler._handle_service_error(error, base_context)
        
        automatic_actions = [a for a in response.corrective_actions if a.is_automatic]
        assert len(automatic_actions) > 0


class TestDataErrorHandling:
    """Test data error handling"""
    
    def test_data_not_found_error(self, error_handler, base_context):
        """Test data not found error handling"""
        error = Exception("Data not found")
        response = error_handler._handle_data_error(error, base_context)
        
        assert response.category == ErrorCategory.DATA
        action_ids = [action.action_id for action in response.corrective_actions]
        assert "use_demo_data" in action_ids or "try_different_query" in action_ids
    
    def test_data_generic_error(self, error_handler, base_context):
        """Test generic data error handling"""
        error = Exception("Database connection failed")
        response = error_handler._handle_data_error(error, base_context)
        
        assert response.category == ErrorCategory.DATA
        assert response.should_retry is True


class TestAuthenticationErrorHandling:
    """Test authentication error handling"""
    
    def test_authentication_error(self, error_handler, base_context):
        """Test authentication error handling"""
        error = Exception("Authentication failed")
        response = error_handler._handle_authentication_error(error, base_context)
        
        assert response.category == ErrorCategory.AUTHENTICATION
        assert response.severity == ErrorSeverity.HIGH
        assert response.can_continue is False  # Cannot continue without auth
        
        action_ids = [action.action_id for action in response.corrective_actions]
        assert "retry_authentication" in action_ids or "use_pin_fallback" in action_ids


class TestValidationErrorHandling:
    """Test validation error handling"""
    
    def test_validation_error(self, error_handler, base_context):
        """Test validation error handling"""
        error = Exception("Invalid input")
        response = error_handler._handle_validation_error(error, base_context)
        
        assert response.category == ErrorCategory.VALIDATION
        assert response.severity == ErrorSeverity.LOW
        assert response.should_retry is False
        assert response.can_continue is True


class TestMultilingualMessages:
    """Test multilingual error messages"""
    
    def test_english_error_message(self, error_handler):
        """Test error message in English"""
        message = error_handler._get_localized_message("network_error", "en")
        assert isinstance(message, str)
        assert len(message) > 0
        assert "network" in message.lower() or "connection" in message.lower()
    
    def test_hindi_error_message(self, error_handler):
        """Test error message in Hindi"""
        message = error_handler._get_localized_message("network_error", "hi")
        assert isinstance(message, str)
        assert len(message) > 0
        # Hindi message should contain Devanagari script
        assert any('\u0900' <= char <= '\u097F' for char in message)
    
    def test_telugu_error_message(self, error_handler):
        """Test error message in Telugu"""
        message = error_handler._get_localized_message("network_error", "te")
        assert isinstance(message, str)
        assert len(message) > 0
        # Telugu message should contain Telugu script
        assert any('\u0C00' <= char <= '\u0C7F' for char in message)
    
    def test_tamil_error_message(self, error_handler):
        """Test error message in Tamil"""
        message = error_handler._get_localized_message("network_error", "ta")
        assert isinstance(message, str)
        assert len(message) > 0
        # Tamil message should contain Tamil script
        assert any('\u0B80' <= char <= '\u0BFF' for char in message)
    
    def test_fallback_to_english(self, error_handler):
        """Test fallback to English for unsupported language"""
        message = error_handler._get_localized_message("network_error", "unsupported_lang")
        assert isinstance(message, str)
        assert len(message) > 0
        # Should fallback to English
        assert message == error_handler._get_localized_message("network_error", "en")
    
    def test_all_error_types_have_messages(self, error_handler):
        """Test all error types have messages in all supported languages"""
        error_keys = [
            "network_error",
            "audio_noise_error",
            "audio_no_speech_error",
            "translation_low_confidence",
            "service_unavailable",
            "data_not_found",
            "authentication_error",
            "validation_error",
            "generic_error",
        ]
        
        languages = ["en", "hi", "te", "ta"]
        
        for lang in languages:
            for key in error_keys:
                message = error_handler._get_localized_message(key, lang)
                assert isinstance(message, str)
                assert len(message) > 0


class TestCorrectiveActions:
    """Test corrective action suggestions"""
    
    def test_corrective_action_structure(self):
        """Test corrective action has required fields"""
        action = CorrectiveAction(
            action_id="test_action",
            description="Test description",
            priority=1,
            is_automatic=False
        )
        
        assert action.action_id == "test_action"
        assert action.description == "Test description"
        assert action.priority == 1
        assert action.is_automatic is False
    
    def test_corrective_action_to_dict(self):
        """Test corrective action conversion to dictionary"""
        action = CorrectiveAction(
            action_id="test_action",
            description="Test description",
            priority=1,
            is_automatic=True
        )
        
        action_dict = action.to_dict()
        assert action_dict["action_id"] == "test_action"
        assert action_dict["description"] == "Test description"
        assert action_dict["priority"] == 1
        assert action_dict["is_automatic"] is True
    
    def test_actions_have_priorities(self, error_handler, base_context):
        """Test corrective actions have priority ordering"""
        error = ConnectionError("Connection timeout")
        response = error_handler._handle_network_error(error, base_context)
        
        for action in response.corrective_actions:
            assert hasattr(action, 'priority')
            assert isinstance(action.priority, int)
            assert action.priority > 0


class TestErrorResponse:
    """Test error response structure"""
    
    def test_error_response_to_dict(self):
        """Test error response conversion to dictionary"""
        actions = [
            CorrectiveAction(
                action_id="action1",
                description="Action 1",
                priority=1
            )
        ]
        
        response = ErrorResponse(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            technical_message="Technical details",
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=5,
            can_continue=True,
            error_code="TEST_001"
        )
        
        response_dict = response.to_dict()
        assert response_dict["category"] == "network"
        assert response_dict["severity"] == "medium"
        assert response_dict["message"] == "Test error message"
        assert response_dict["should_retry"] is True
        assert response_dict["retry_after_seconds"] == 5
        assert response_dict["can_continue"] is True
        assert response_dict["error_code"] == "TEST_001"
        assert len(response_dict["corrective_actions"]) == 1


class TestPrivacyPreservingLogging:
    """Test privacy-preserving error logging (Requirement 14.4)"""
    
    def test_log_does_not_contain_user_id(self, error_handler, base_context, caplog):
        """Test error logs do not contain user IDs"""
        import logging
        caplog.set_level(logging.ERROR)
        
        error = Exception("Test error")
        error_handler._log_error_safely(error, base_context, ErrorCategory.NETWORK)
        
        # Check that user_id is not in log messages
        for record in caplog.records:
            assert base_context.user_id not in record.message
            if hasattr(record, 'context'):
                assert 'user_id' not in record.context
    
    def test_log_does_not_contain_conversation_id(self, error_handler, base_context, caplog):
        """Test error logs do not contain conversation IDs"""
        import logging
        caplog.set_level(logging.ERROR)
        
        error = Exception("Test error")
        error_handler._log_error_safely(error, base_context, ErrorCategory.NETWORK)
        
        # Check that conversation_id is not in log messages
        for record in caplog.records:
            assert base_context.conversation_id not in record.message
            if hasattr(record, 'context'):
                assert 'conversation_id' not in record.context
    
    def test_log_contains_safe_context(self, error_handler, base_context, caplog):
        """Test error logs contain safe context information"""
        import logging
        caplog.set_level(logging.ERROR)
        
        error = Exception("Test error")
        error_handler._log_error_safely(error, base_context, ErrorCategory.NETWORK)
        
        # Should log category and operation (non-PII)
        assert len(caplog.records) > 0
        # The error type should be logged
        assert "Exception" in caplog.text or "Error" in caplog.text



class TestEndToEndErrorHandling:
    """Test end-to-end error handling flow"""
    
    def test_handle_error_network(self, error_handler, base_context):
        """Test handling network error end-to-end"""
        error = ConnectionError("Connection timeout")
        response = error_handler.handle_error(error, base_context)
        
        assert response.category == ErrorCategory.NETWORK
        assert isinstance(response.message, str)
        assert len(response.corrective_actions) > 0
    
    def test_handle_error_audio(self, error_handler, base_context):
        """Test handling audio error end-to-end"""
        error = Exception("Audio quality poor")
        response = error_handler.handle_error(error, base_context)
        
        assert response.category == ErrorCategory.AUDIO
        assert isinstance(response.message, str)
        assert len(response.corrective_actions) > 0
    
    def test_handle_error_with_different_languages(self, error_handler):
        """Test error handling with different user languages"""
        error = ConnectionError("Connection timeout")
        
        # Test with English
        context_en = ErrorContext(user_language="en", operation="test")
        response_en = error_handler.handle_error(error, context_en)
        assert "network" in response_en.message.lower() or "connection" in response_en.message.lower()
        
        # Test with Hindi
        context_hi = ErrorContext(user_language="hi", operation="test")
        response_hi = error_handler.handle_error(error, context_hi)
        assert any('\u0900' <= char <= '\u097F' for char in response_hi.message)
        
        # Messages should be different
        assert response_en.message != response_hi.message
    
    def test_handle_error_returns_valid_response(self, error_handler, base_context):
        """Test all error types return valid responses"""
        test_errors = [
            ConnectionError("Network error"),
            Exception("Audio quality poor"),
            Exception("Translation failed"),
            Exception("Service unavailable"),
            Exception("Data not found"),
            Exception("Authentication failed"),
            Exception("Invalid input"),
            Exception("Unknown error"),
        ]
        
        for error in test_errors:
            response = error_handler.handle_error(error, base_context)
            
            # Validate response structure
            assert isinstance(response, ErrorResponse)
            assert isinstance(response.category, ErrorCategory)
            assert isinstance(response.severity, ErrorSeverity)
            assert isinstance(response.message, str)
            assert len(response.message) > 0
            assert isinstance(response.corrective_actions, list)
            assert isinstance(response.should_retry, bool)
            assert isinstance(response.can_continue, bool)


class TestErrorContext:
    """Test error context"""
    
    def test_error_context_creation(self):
        """Test error context creation"""
        context = ErrorContext(
            user_id="user123",
            user_language="hi",
            conversation_id="conv456",
            operation="price_query"
        )
        
        assert context.user_id == "user123"
        assert context.user_language == "hi"
        assert context.conversation_id == "conv456"
        assert context.operation == "price_query"
        assert context.timestamp is not None
    
    def test_error_context_to_dict(self):
        """Test error context conversion to dictionary"""
        context = ErrorContext(
            user_id="user123",
            user_language="hi",
            operation="price_query"
        )
        
        context_dict = context.to_dict()
        assert context_dict["user_id"] == "user123"
        assert context_dict["user_language"] == "hi"
        assert context_dict["operation"] == "price_query"
        assert "timestamp" in context_dict
