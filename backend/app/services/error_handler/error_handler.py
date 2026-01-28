"""Centralized error handling service with multilingual support

This service provides:
- Error categorization (network, audio, translation, service, data)
- Multilingual error messages
- Corrective action suggestions
- Privacy-preserving error logging

Requirements: 14.1, 14.2
"""
import logging
from typing import Optional, Dict, List
from .models import (
    ErrorCategory,
    ErrorSeverity,
    ErrorResponse,
    ErrorContext,
    CorrectiveAction,
)


logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling service"""
    
    def __init__(self):
        """Initialize error handler with multilingual messages"""
        self.error_messages = self._load_error_messages()
        self.corrective_actions = self._load_corrective_actions()
    
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """
        Routes errors to appropriate handlers
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            ErrorResponse with user-facing message and recovery actions
        """
        # Categorize the error
        category = self._categorize_error(error)
        
        # Route to specific handler
        if category == ErrorCategory.NETWORK:
            return self._handle_network_error(error, context)
        elif category == ErrorCategory.AUDIO:
            return self._handle_audio_error(error, context)
        elif category == ErrorCategory.TRANSLATION:
            return self._handle_translation_error(error, context)
        elif category == ErrorCategory.SERVICE:
            return self._handle_service_error(error, context)
        elif category == ErrorCategory.DATA:
            return self._handle_data_error(error, context)
        elif category == ErrorCategory.AUTHENTICATION:
            return self._handle_authentication_error(error, context)
        elif category == ErrorCategory.VALIDATION:
            return self._handle_validation_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorizes an error based on its type and message
        
        Args:
            error: The exception to categorize
            
        Returns:
            ErrorCategory enum value
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # Network errors
        if any(keyword in error_type.lower() for keyword in ['network', 'connection', 'timeout']):
            return ErrorCategory.NETWORK
        if any(keyword in error_msg for keyword in ['connection', 'timeout', 'network', 'offline']):
            return ErrorCategory.NETWORK
        
        # Audio errors
        if any(keyword in error_type.lower() for keyword in ['audio', 'speech', 'microphone']):
            return ErrorCategory.AUDIO
        if any(keyword in error_msg for keyword in ['audio', 'noise', 'speech', 'microphone', 'recording']):
            return ErrorCategory.AUDIO
        
        # Translation errors
        if any(keyword in error_type.lower() for keyword in ['translation', 'language']):
            return ErrorCategory.TRANSLATION
        if any(keyword in error_msg for keyword in ['translation', 'transcription', 'language']):
            return ErrorCategory.TRANSLATION
        
        # Service errors
        if any(keyword in error_type.lower() for keyword in ['service', 'unavailable', 'api']):
            return ErrorCategory.SERVICE
        if any(keyword in error_msg for keyword in ['service', 'unavailable', 'api', 'model']):
            return ErrorCategory.SERVICE
        
        # Data errors
        if any(keyword in error_type.lower() for keyword in ['data', 'database', 'validation']):
            return ErrorCategory.DATA
        if any(keyword in error_msg for keyword in ['data', 'database', 'price', 'not found']):
            return ErrorCategory.DATA
        
        # Authentication errors
        if any(keyword in error_type.lower() for keyword in ['auth', 'permission', 'unauthorized']):
            return ErrorCategory.AUTHENTICATION
        if any(keyword in error_msg for keyword in ['auth', 'permission', 'unauthorized', 'forbidden']):
            return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if any(keyword in error_type.lower() for keyword in ['validation', 'invalid']):
            return ErrorCategory.VALIDATION
        if any(keyword in error_msg for keyword in ['invalid', 'validation', 'required']):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    def _handle_network_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """
        Handle network-related errors
        
        Strategy:
        1. Switch to offline mode
        2. Queue pending operations
        3. Notify user in their language
        4. Provide cached data if available
        """
        # Log error (without PII)
        self._log_error_safely(error, context, ErrorCategory.NETWORK)
        
        # Get localized message
        message = self._get_localized_message(
            "network_error",
            context.user_language
        )
        
        # Get corrective actions
        actions = [
            CorrectiveAction(
                action_id="check_connection",
                description="Check your internet connection",
                priority=1
            ),
            CorrectiveAction(
                action_id="switch_offline",
                description="Switch to offline mode to continue",
                priority=2,
                is_automatic=True
            ),
            CorrectiveAction(
                action_id="retry_later",
                description="Try again when connection is restored",
                priority=3
            ),
        ]
        
        return ErrorResponse(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=5,
            can_continue=True,
            error_code="NET_001"
        )
    
    def _handle_audio_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """
        Handle audio processing errors
        
        Strategy:
        1. Provide specific feedback (too noisy, too quiet, etc.)
        2. Suggest corrective actions
        3. Request user to repeat
        """
        self._log_error_safely(error, context, ErrorCategory.AUDIO)
        
        error_msg = str(error).lower()
        
        # Determine specific audio issue
        if "noise" in error_msg or "quality" in error_msg:
            message_key = "audio_noise_error"
            actions = [
                CorrectiveAction(
                    action_id="reduce_noise",
                    description="Move to a quieter location",
                    priority=1
                ),
                CorrectiveAction(
                    action_id="speak_closer",
                    description="Speak closer to the microphone",
                    priority=2
                ),
                CorrectiveAction(
                    action_id="retry_recording",
                    description="Try recording again",
                    priority=3
                ),
            ]
        elif "no speech" in error_msg or "silence" in error_msg:
            message_key = "audio_no_speech_error"
            actions = [
                CorrectiveAction(
                    action_id="check_microphone",
                    description="Check if microphone is working",
                    priority=1
                ),
                CorrectiveAction(
                    action_id="speak_louder",
                    description="Speak louder and clearer",
                    priority=2
                ),
                CorrectiveAction(
                    action_id="retry_recording",
                    description="Try recording again",
                    priority=3
                ),
            ]
        else:
            message_key = "audio_generic_error"
            actions = [
                CorrectiveAction(
                    action_id="check_microphone",
                    description="Check microphone permissions and settings",
                    priority=1
                ),
                CorrectiveAction(
                    action_id="retry_recording",
                    description="Try recording again",
                    priority=2
                ),
            ]
        
        message = self._get_localized_message(message_key, context.user_language)
        
        return ErrorResponse(
            category=ErrorCategory.AUDIO,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=0,
            can_continue=True,
            error_code="AUD_001"
        )
    
    def _handle_translation_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """Handle translation/transcription errors"""
        self._log_error_safely(error, context, ErrorCategory.TRANSLATION)
        
        error_msg = str(error).lower()
        
        if "confidence" in error_msg or "low quality" in error_msg:
            message_key = "translation_low_confidence"
            actions = [
                CorrectiveAction(
                    action_id="confirm_message",
                    description="Please confirm if the message is correct",
                    priority=1
                ),
                CorrectiveAction(
                    action_id="speak_again",
                    description="Speak again more clearly",
                    priority=2
                ),
            ]
        else:
            message_key = "translation_generic_error"
            actions = [
                CorrectiveAction(
                    action_id="retry_translation",
                    description="Try again",
                    priority=1
                ),
            ]
        
        message = self._get_localized_message(message_key, context.user_language)
        
        return ErrorResponse(
            category=ErrorCategory.TRANSLATION,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=0,
            can_continue=True,
            error_code="TRN_001"
        )
    
    def _handle_service_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """
        Handle service unavailability errors
        
        Strategy:
        1. Retry with exponential backoff
        2. Degrade to cached/offline mode
        3. Notify user of degraded functionality
        """
        self._log_error_safely(error, context, ErrorCategory.SERVICE)
        
        message = self._get_localized_message("service_unavailable", context.user_language)
        
        actions = [
            CorrectiveAction(
                action_id="retry_service",
                description="Retrying automatically...",
                priority=1,
                is_automatic=True
            ),
            CorrectiveAction(
                action_id="use_cached_data",
                description="Using cached data",
                priority=2,
                is_automatic=True
            ),
            CorrectiveAction(
                action_id="try_later",
                description="Try again later",
                priority=3
            ),
        ]
        
        return ErrorResponse(
            category=ErrorCategory.SERVICE,
            severity=ErrorSeverity.HIGH,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=2,
            can_continue=True,
            error_code="SVC_001"
        )
    
    def _handle_data_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """Handle data-related errors"""
        self._log_error_safely(error, context, ErrorCategory.DATA)
        
        error_msg = str(error).lower()
        
        if "not found" in error_msg or "unavailable" in error_msg:
            message_key = "data_not_found"
            actions = [
                CorrectiveAction(
                    action_id="use_demo_data",
                    description="Using demo data as fallback",
                    priority=1,
                    is_automatic=True
                ),
                CorrectiveAction(
                    action_id="try_different_query",
                    description="Try a different search",
                    priority=2
                ),
            ]
        else:
            message_key = "data_generic_error"
            actions = [
                CorrectiveAction(
                    action_id="retry_query",
                    description="Try again",
                    priority=1
                ),
            ]
        
        message = self._get_localized_message(message_key, context.user_language)
        
        return ErrorResponse(
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=1,
            can_continue=True,
            error_code="DAT_001"
        )
    
    def _handle_authentication_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """Handle authentication errors"""
        self._log_error_safely(error, context, ErrorCategory.AUTHENTICATION)
        
        message = self._get_localized_message("authentication_error", context.user_language)
        
        actions = [
            CorrectiveAction(
                action_id="retry_authentication",
                description="Try authenticating again",
                priority=1
            ),
            CorrectiveAction(
                action_id="use_pin_fallback",
                description="Use voice PIN as fallback",
                priority=2
            ),
        ]
        
        return ErrorResponse(
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=0,
            can_continue=False,
            error_code="AUTH_001"
        )
    
    def _handle_validation_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """Handle validation errors"""
        self._log_error_safely(error, context, ErrorCategory.VALIDATION)
        
        message = self._get_localized_message("validation_error", context.user_language)
        
        actions = [
            CorrectiveAction(
                action_id="provide_valid_input",
                description="Please provide valid input",
                priority=1
            ),
        ]
        
        return ErrorResponse(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=False,
            can_continue=True,
            error_code="VAL_001"
        )
    
    def _handle_generic_error(
        self,
        error: Exception,
        context: ErrorContext
    ) -> ErrorResponse:
        """Handle unknown/generic errors"""
        self._log_error_safely(error, context, ErrorCategory.UNKNOWN)
        
        message = self._get_localized_message("generic_error", context.user_language)
        
        actions = [
            CorrectiveAction(
                action_id="retry_operation",
                description="Try again",
                priority=1
            ),
            CorrectiveAction(
                action_id="contact_support",
                description="Contact support if problem persists",
                priority=2
            ),
        ]
        
        return ErrorResponse(
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            message=message,
            technical_message=str(error),
            corrective_actions=actions,
            should_retry=True,
            retry_after_seconds=1,
            can_continue=True,
            error_code="UNK_001"
        )
    
    def _log_error_safely(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory
    ):
        """
        Log error without exposing PII
        
        Requirements: 14.4 - Privacy-preserving error logging
        """
        # Create sanitized context (remove PII)
        safe_context = {
            "category": category.value,
            "operation": context.operation,
            "timestamp": context.timestamp.isoformat() if context.timestamp else None,
            "user_language": context.user_language,
            # Do NOT log user_id, conversation_id, or other PII
        }
        
        # Log with sanitized context
        logger.error(
            f"Error occurred: {type(error).__name__}",
            extra={
                "error_category": category.value,
                "context": safe_context,
                "error_type": type(error).__name__,
            }
        )
    
    def _get_localized_message(
        self,
        message_key: str,
        language: str
    ) -> str:
        """
        Get error message in user's language
        
        Args:
            message_key: Key for the error message
            language: ISO language code
            
        Returns:
            Localized error message
        """
        # Get messages for the language, fallback to English
        lang_messages = self.error_messages.get(language, self.error_messages.get("en", {}))
        
        # Get specific message, fallback to generic
        message = lang_messages.get(message_key, lang_messages.get("generic_error", "An error occurred"))
        
        return message
    
    def _load_error_messages(self) -> Dict[str, Dict[str, str]]:
        """
        Load multilingual error messages
        
        Returns:
            Dictionary mapping language codes to error messages
        """
        return {
            "en": {
                "network_error": "Network connection lost. Your messages will be sent when connection is restored.",
                "audio_noise_error": "Audio quality is poor due to background noise. Please move to a quieter location and try again.",
                "audio_no_speech_error": "No speech detected. Please check your microphone and speak clearly.",
                "audio_generic_error": "Could not process audio. Please check your microphone and try again.",
                "translation_low_confidence": "Translation may not be accurate. Please confirm the message.",
                "translation_generic_error": "Translation failed. Please try again.",
                "service_unavailable": "Service is temporarily unavailable. Retrying automatically...",
                "data_not_found": "Requested data not found. Using demo data as fallback.",
                "data_generic_error": "Could not retrieve data. Please try again.",
                "authentication_error": "Authentication failed. Please try again or use voice PIN.",
                "validation_error": "Invalid input. Please provide correct information.",
                "generic_error": "An error occurred. Please try again.",
            },
            "hi": {  # Hindi
                "network_error": "नेटवर्क कनेक्शन टूट गया है। कनेक्शन बहाल होने पर आपके संदेश भेजे जाएंगे।",
                "audio_noise_error": "पृष्ठभूमि शोर के कारण ऑडियो गुणवत्ता खराब है। कृपया शांत स्थान पर जाएं और पुनः प्रयास करें।",
                "audio_no_speech_error": "कोई आवाज़ नहीं मिली। कृपया अपना माइक्रोफ़ोन जांचें और स्पष्ट रूप से बोलें।",
                "audio_generic_error": "ऑडियो प्रोसेस नहीं हो सका। कृपया अपना माइक्रोफ़ोन जांचें और पुनः प्रयास करें।",
                "translation_low_confidence": "अनुवाद सटीक नहीं हो सकता। कृपया संदेश की पुष्टि करें।",
                "translation_generic_error": "अनुवाद विफल रहा। कृपया पुनः प्रयास करें।",
                "service_unavailable": "सेवा अस्थायी रूप से अनुपलब्ध है। स्वचालित रूप से पुनः प्रयास कर रहे हैं...",
                "data_not_found": "अनुरोधित डेटा नहीं मिला। डेमो डेटा का उपयोग कर रहे हैं।",
                "data_generic_error": "डेटा प्राप्त नहीं हो सका। कृपया पुनः प्रयास करें।",
                "authentication_error": "प्रमाणीकरण विफल रहा। कृपया पुनः प्रयास करें या वॉयस पिन का उपयोग करें।",
                "validation_error": "अमान्य इनपुट। कृपया सही जानकारी प्रदान करें।",
                "generic_error": "एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
            },
            "te": {  # Telugu
                "network_error": "నెట్‌వర్క్ కనెక్షన్ కోల్పోయింది. కనెక్షన్ పునరుద్ధరించబడినప్పుడు మీ సందేశాలు పంపబడతాయి.",
                "audio_noise_error": "నేపథ్య శబ్దం కారణంగా ఆడియో నాణ్యత తక్కువగా ఉంది. దయచేసి నిశ్శబ్ద ప్రదేశానికి వెళ్లి మళ్లీ ప్రయత్నించండి.",
                "audio_no_speech_error": "ప్రసంగం గుర్తించబడలేదు. దయచేసి మీ మైక్రోఫోన్‌ను తనిఖీ చేసి స్పష్టంగా మాట్లాడండి.",
                "audio_generic_error": "ఆడియో ప్రాసెస్ చేయలేకపోయింది. దయచేసి మీ మైక్రోఫోన్‌ను తనిఖీ చేసి మళ్లీ ప్రయత్నించండి.",
                "translation_low_confidence": "అనువాదం ఖచ్చితమైనది కాకపోవచ్చు. దయచేసి సందేశాన్ని నిర్ధారించండి.",
                "translation_generic_error": "అనువాదం విఫలమైంది. దయచేసి మళ్లీ ప్రయత్నించండి.",
                "service_unavailable": "సేవ తాత్కాలికంగా అందుబాటులో లేదు. స్వయంచాలకంగా మళ్లీ ప్రయత్నిస్తోంది...",
                "data_not_found": "అభ్యర్థించిన డేటా కనుగొనబడలేదు. డెమో డేటాను ఉపయోగిస్తోంది.",
                "data_generic_error": "డేటాను తిరిగి పొందలేకపోయింది. దయచేసి మళ్లీ ప్రయత్నించండి.",
                "authentication_error": "ప్రమాణీకరణ విఫలమైంది. దయచేసి మళ్లీ ప్రయత్నించండి లేదా వాయిస్ పిన్ ఉపయోగించండి.",
                "validation_error": "చెల్లని ఇన్‌పుట్. దయచేసి సరైన సమాచారాన్ని అందించండి.",
                "generic_error": "లోపం సంభవించింది. దయచేసి మళ్లీ ప్రయత్నించండి.",
            },
            "ta": {  # Tamil
                "network_error": "நெட்வொர்க் இணைப்பு துண்டிக்கப்பட்டது. இணைப்பு மீட்டெடுக்கப்படும்போது உங்கள் செய்திகள் அனுப்பப்படும்.",
                "audio_noise_error": "பின்னணி சத்தம் காரணமாக ஆடியோ தரம் மோசமாக உள்ளது. தயவுசெய்து அமைதியான இடத்திற்குச் சென்று மீண்டும் முயற்சிக்கவும்.",
                "audio_no_speech_error": "பேச்சு கண்டறியப்படவில்லை. தயவுசெய்து உங்கள் மைக்ரோஃபோனை சரிபார்த்து தெளிவாகப் பேசவும்.",
                "audio_generic_error": "ஆடியோவை செயலாக்க முடியவில்லை. தயவுசெய்து உங்கள் மைக்ரோஃபோனை சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
                "translation_low_confidence": "மொழிபெயர்ப்பு துல்லியமாக இல்லாமல் இருக்கலாம். தயவுசெய்து செய்தியை உறுதிப்படுத்தவும்.",
                "translation_generic_error": "மொழிபெயர்ப்பு தோல்வியடைந்தது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
                "service_unavailable": "சேவை தற்காலிகமாக கிடைக்கவில்லை. தானாகவே மீண்டும் முயற்சிக்கிறது...",
                "data_not_found": "கோரப்பட்ட தரவு கிடைக்கவில்லை. டெமோ தரவைப் பயன்படுத்துகிறது.",
                "data_generic_error": "தரவை மீட்டெடுக்க முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
                "authentication_error": "அங்கீகாரம் தோல்வியடைந்தது. தயவுசெய்து மீண்டும் முயற்சிக்கவும் அல்லது குரல் பின் பயன்படுத்தவும்.",
                "validation_error": "தவறான உள்ளீடு. தயவுசெய்து சரியான தகவலை வழங்கவும்.",
                "generic_error": "பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
            },
        }
    
    def _load_corrective_actions(self) -> Dict[str, List[CorrectiveAction]]:
        """Load predefined corrective actions"""
        return {}  # Actions are created dynamically based on error type
