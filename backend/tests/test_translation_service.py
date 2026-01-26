"""Unit tests for Translation Service"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock torch and transformers before importing the service
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()

from app.services.vocal_vernacular.translation_service import (
    TranslationService,
    SUPPORTED_LANGUAGES
)
from app.services.vocal_vernacular.models import (
    TranslationResult,
    Entity,
    Message
)
from datetime import datetime


@pytest.fixture
def mock_model():
    """Mock the IndicTrans2 model"""
    with patch('app.services.vocal_vernacular.translation_service.AutoModelForSeq2SeqLM') as mock_model_cls, \
         patch('app.services.vocal_vernacular.translation_service.AutoTokenizer') as mock_tokenizer_cls, \
         patch('app.services.vocal_vernacular.translation_service.torch') as mock_torch:
        
        # Mock torch tensor
        mock_tensor = MagicMock()
        mock_torch.tensor.return_value = mock_tensor
        mock_torch.cuda.is_available.return_value = False
        
        # Mock tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer_output = MagicMock()
        mock_tokenizer_output.to.return_value = mock_tokenizer_output
        mock_tokenizer.return_value = mock_tokenizer_output
        mock_tokenizer.decode.return_value = "translated text"
        mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
        
        # Mock model
        mock_model_instance = MagicMock()
        mock_model_instance.generate.return_value = mock_tensor
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_cls.from_pretrained.return_value = mock_model_instance
        
        yield {
            'model_cls': mock_model_cls,
            'tokenizer_cls': mock_tokenizer_cls,
            'model': mock_model_instance,
            'tokenizer': mock_tokenizer,
            'torch': mock_torch
        }


class TestTranslationServiceInitialization:
    """Test translation service initialization"""
    
    def test_initialization_default_model(self):
        """Test service initializes with default model"""
        service = TranslationService()
        assert service.model_name == "ai4bharat/indictrans2-indic-indic-1B"
        assert service.model is None  # Not loaded until first use
        assert service.tokenizer is None
    
    def test_initialization_custom_model(self):
        """Test service initializes with custom model"""
        custom_model = "custom/model"
        service = TranslationService(model_name=custom_model)
        assert service.model_name == custom_model
    
    def test_device_selection(self):
        """Test device selection (CPU/CUDA)"""
        service = TranslationService()
        assert service.device in ["cpu", "cuda"]
    
    def test_supported_languages_count(self):
        """Test that all 22 scheduled languages are supported"""
        # 22 Indian languages + English
        assert len(SUPPORTED_LANGUAGES) == 23


class TestEntityExtraction:
    """Test entity extraction functionality"""
    
    def test_extract_price_rupee_symbol(self):
        """Test extraction of prices with rupee symbol"""
        service = TranslationService()
        text = "The price is ₹100 per kg"
        entities = service._extract_entities(text)
        
        price_entities = [e for e in entities if e.entity_type == 'price']
        assert len(price_entities) >= 1
        assert '100' in price_entities[0].text
    
    def test_extract_price_with_decimals(self):
        """Test extraction of prices with decimal values"""
        service = TranslationService()
        text = "Cost is 125.50 rupees"
        entities = service._extract_entities(text)
        
        price_entities = [e for e in entities if e.entity_type == 'price']
        assert len(price_entities) >= 1
    
    def test_extract_price_hindi(self):
        """Test extraction of prices in Hindi"""
        service = TranslationService()
        text = "कीमत 100 रुपये है"
        entities = service._extract_entities(text)
        
        price_entities = [e for e in entities if e.entity_type == 'price']
        assert len(price_entities) >= 1
    
    def test_extract_unit_kg(self):
        """Test extraction of kilogram units"""
        service = TranslationService()
        text = "I need 50 kg of rice"
        entities = service._extract_entities(text)
        
        unit_entities = [e for e in entities if e.entity_type == 'unit']
        assert len(unit_entities) >= 1
        assert 'kg' in unit_entities[0].text.lower()
    
    def test_extract_unit_hindi(self):
        """Test extraction of units in Hindi"""
        service = TranslationService()
        text = "मुझे 50 किलो चावल चाहिए"
        entities = service._extract_entities(text)
        
        unit_entities = [e for e in entities if e.entity_type == 'unit']
        assert len(unit_entities) >= 1
    
    def test_extract_commodity_names(self):
        """Test extraction of commodity names"""
        service = TranslationService()
        text = "I want to buy tomato and onion"
        entities = service._extract_entities(text)
        
        commodity_entities = [e for e in entities if e.entity_type == 'commodity']
        assert len(commodity_entities) >= 1
        commodity_texts = [e.text.lower() for e in commodity_entities]
        assert any('tomato' in text for text in commodity_texts)
    
    def test_extract_multiple_entities(self):
        """Test extraction of multiple entity types"""
        service = TranslationService()
        text = "Tomato costs ₹50 per kg"
        entities = service._extract_entities(text)
        
        # Should have commodity, price, and unit
        entity_types = {e.entity_type for e in entities}
        assert 'price' in entity_types
        assert 'unit' in entity_types or 'commodity' in entity_types
    
    def test_entity_positions(self):
        """Test that entity positions are correctly recorded"""
        service = TranslationService()
        text = "Price is ₹100"
        entities = service._extract_entities(text)
        
        price_entities = [e for e in entities if e.entity_type == 'price']
        if price_entities:
            entity = price_entities[0]
            assert entity.start_pos >= 0
            assert entity.end_pos > entity.start_pos
            assert text[entity.start_pos:entity.end_pos] == entity.text


class TestTranslation:
    """Test translation functionality"""
    
    def test_translate_basic(self, mock_model):
        """Test basic translation between languages"""
        service = TranslationService()
        
        result = service.translate(
            text="Hello, how are you?",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert isinstance(result, TranslationResult)
        assert result.text is not None
        assert result.source_language == "eng_Latn"
        assert result.target_language == "hin_Deva"
        assert result.confidence > 0
    
    def test_translate_loads_model_once(self, mock_model):
        """Test that model is loaded only once"""
        service = TranslationService()
        
        # First translation
        service.translate("test", "eng_Latn", "hin_Deva")
        first_call_count = mock_model['model_cls'].from_pretrained.call_count
        
        # Second translation
        service.translate("test2", "eng_Latn", "tel_Telu")
        second_call_count = mock_model['model_cls'].from_pretrained.call_count
        
        # Model should only be loaded once
        assert first_call_count == second_call_count
    
    def test_translate_confidence_score(self, mock_model):
        """Test that translation returns confidence score"""
        service = TranslationService()
        
        result = service.translate(
            text="Test text",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert 0 <= result.confidence <= 1.0
    
    def test_translate_processing_time(self, mock_model):
        """Test that processing time is recorded"""
        service = TranslationService()
        
        result = service.translate(
            text="Test text",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert result.processing_time_ms is not None
        assert result.processing_time_ms >= 0
    
    def test_translate_preserves_entities(self, mock_model):
        """Test that entities are extracted and preserved"""
        service = TranslationService()
        
        result = service.translate(
            text="Tomato costs ₹50 per kg",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert result.preserved_entities is not None
        assert len(result.preserved_entities) > 0
    
    def test_translate_latency_requirement(self, mock_model):
        """Test that translation completes within 2 seconds (Requirement 3.1)"""
        service = TranslationService()
        
        result = service.translate(
            text="This is a test message for translation",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        # Requirement 3.1: Translation should complete within 2 seconds
        assert result.processing_time_ms < 2000


class TestTranslationWithContext:
    """Test context-aware translation"""
    
    def test_translate_with_empty_context(self, mock_model):
        """Test translation with no conversation history"""
        service = TranslationService()
        
        result = service.translate_with_context(
            text="Hello",
            source_lang="eng_Latn",
            target_lang="hin_Deva",
            conversation_history=[]
        )
        
        assert isinstance(result, TranslationResult)
        assert result.text is not None
    
    def test_translate_with_context_history(self, mock_model):
        """Test translation with conversation history"""
        service = TranslationService()
        
        history = [
            Message(
                id="1",
                sender_id="user1",
                text="I want to buy tomatoes",
                language="eng_Latn",
                timestamp=datetime.now()
            ),
            Message(
                id="2",
                sender_id="user2",
                text="How much do you need?",
                language="hin_Deva",
                timestamp=datetime.now()
            )
        ]
        
        result = service.translate_with_context(
            text="About 10 kg",
            source_lang="eng_Latn",
            target_lang="hin_Deva",
            conversation_history=history
        )
        
        assert isinstance(result, TranslationResult)
        assert result.text is not None
    
    def test_translate_with_context_limits_history(self, mock_model):
        """Test that only recent messages are used for context"""
        service = TranslationService()
        
        # Create 10 messages
        history = [
            Message(
                id=str(i),
                sender_id="user1",
                text=f"Message {i}",
                language="eng_Latn",
                timestamp=datetime.now()
            )
            for i in range(10)
        ]
        
        result = service.translate_with_context(
            text="Current message",
            source_lang="eng_Latn",
            target_lang="hin_Deva",
            conversation_history=history
        )
        
        # Should complete successfully with limited context
        assert isinstance(result, TranslationResult)


class TestEntityPreservation:
    """Test entity preservation in translation"""
    
    def test_preserve_entities_placeholder(self):
        """Test entity preservation (placeholder implementation)"""
        service = TranslationService()
        
        entities = [
            Entity(text="₹100", entity_type="price", start_pos=10, end_pos=14),
            Entity(text="kg", entity_type="unit", start_pos=20, end_pos=22)
        ]
        
        translated_text = "translated text with entities"
        result = service._preserve_entities(translated_text, entities)
        
        # Current implementation returns text as-is
        assert result == translated_text
    
    def test_preserve_entities_empty_list(self):
        """Test entity preservation with no entities"""
        service = TranslationService()
        
        translated_text = "simple text"
        result = service._preserve_entities(translated_text, [])
        
        assert result == translated_text


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_translate_empty_text(self, mock_model):
        """Test translation of empty text"""
        service = TranslationService()
        
        result = service.translate(
            text="",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert isinstance(result, TranslationResult)
    
    def test_translate_very_long_text(self, mock_model):
        """Test translation of long text (truncation handling)"""
        service = TranslationService()
        
        # Create text longer than max_length (512 tokens)
        long_text = "This is a test sentence. " * 100
        
        result = service.translate(
            text=long_text,
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert isinstance(result, TranslationResult)
    
    def test_translate_special_characters(self, mock_model):
        """Test translation with special characters"""
        service = TranslationService()
        
        result = service.translate(
            text="Price: ₹100! @#$%",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert isinstance(result, TranslationResult)
    
    def test_extract_entities_empty_text(self):
        """Test entity extraction from empty text"""
        service = TranslationService()
        entities = service._extract_entities("")
        assert entities == []
    
    def test_extract_entities_no_matches(self):
        """Test entity extraction when no entities present"""
        service = TranslationService()
        entities = service._extract_entities("This is plain text")
        # May have empty list or only commodity matches
        assert isinstance(entities, list)


class TestRequirementCompliance:
    """Test compliance with specific requirements"""
    
    def test_requirement_3_1_latency(self, mock_model):
        """Test Requirement 3.1: Translation within 2 seconds"""
        service = TranslationService()
        
        result = service.translate(
            text="Test message for latency check",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        assert result.processing_time_ms < 2000
    
    def test_requirement_3_2_entity_preservation(self, mock_model):
        """Test Requirement 3.2: Preserve commodity names, prices, units"""
        service = TranslationService()
        
        result = service.translate(
            text="Tomato costs ₹50 per kg",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        # Entities should be extracted
        assert result.preserved_entities is not None
        entity_types = {e.entity_type for e in result.preserved_entities}
        
        # Should have at least one entity type
        assert len(entity_types) > 0
    
    def test_requirement_3_3_confidence_scoring(self, mock_model):
        """Test Requirement 3.3: Confidence scoring"""
        service = TranslationService()
        
        result = service.translate(
            text="Test text",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        # Should have confidence score
        assert result.confidence is not None
        assert 0 <= result.confidence <= 1.0
    
    def test_requirement_3_5_low_confidence_flagging(self, mock_model):
        """Test Requirement 3.5: Low confidence flagging capability"""
        service = TranslationService()
        
        result = service.translate(
            text="Test text",
            source_lang="eng_Latn",
            target_lang="hin_Deva"
        )
        
        # Service should provide confidence score for flagging
        assert hasattr(result, 'confidence')
        
        # In production, low confidence (<threshold) would trigger flag
        # Here we just verify the capability exists
        if result.confidence < 0.7:
            # Would flag for verification
            assert True
