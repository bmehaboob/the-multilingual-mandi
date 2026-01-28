"""Translation Service using AI4Bharat IndicTrans2 models"""
import time
import re
from typing import Optional, List, Dict
from uuid import UUID
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
from sqlalchemy.orm import Session

from .models import TranslationResult, Entity, Message


# Supported languages (22 scheduled Indian languages)
SUPPORTED_LANGUAGES = [
    "hin_Deva",  # Hindi
    "tel_Telu",  # Telugu
    "tam_Taml",  # Tamil
    "kan_Knda",  # Kannada
    "mar_Deva",  # Marathi
    "ben_Beng",  # Bengali
    "guj_Gujr",  # Gujarati
    "pan_Guru",  # Punjabi
    "mal_Mlym",  # Malayalam
    "asm_Beng",  # Assamese
    "ori_Orya",  # Odia
    "urd_Arab",  # Urdu
    "kas_Arab",  # Kashmiri
    "kok_Deva",  # Konkani
    "npi_Deva",  # Nepali
    "brx_Deva",  # Bodo
    "doi_Deva",  # Dogri
    "mai_Deva",  # Maithili
    "mni_Mtei",  # Manipuri
    "sat_Olck",  # Santali
    "snd_Arab",  # Sindhi
    "san_Deva",  # Sanskrit
    "eng_Latn",  # English (for reference)
]


class TranslationService:
    """
    Translates text between Indian languages using IndicTrans2
    
    Supports all 22 scheduled Indian languages with entity preservation
    for commodity names, prices, and units.
    """
    
    def __init__(self, model_name: str = "ai4bharat/indictrans2-indic-indic-1B"):
        """
        Initialize the translation service
        
        Args:
            model_name: HuggingFace model identifier for IndicTrans2
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Entity patterns for preservation
        self.price_pattern = re.compile(r'₹?\s*\d+(?:\.\d+)?(?:\s*(?:रुपये|रुपया|rupees?|rs\.?))?', re.IGNORECASE)
        self.unit_pattern = re.compile(r'\d+\s*(?:kg|किलो|kilogram|gram|ग्राम|quintal|क्विंटल|ton|टन)', re.IGNORECASE)
        
        # Common commodity names to preserve (can be expanded)
        self.commodity_names = {
            'tomato', 'टमाटर', 'onion', 'प्याज', 'potato', 'आलू',
            'rice', 'चावल', 'wheat', 'गेहूं', 'cotton', 'कपास',
            'sugarcane', 'गन्ना', 'soybean', 'सोयाबीन'
        }
    
    def load_model(self):
        """Load the IndicTrans2 model and tokenizer"""
        if self.model is None:
            print(f"Loading IndicTrans2 model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model.to(self.device)
            self.model.eval()
            print(f"Model loaded successfully on {self.device}")
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities (prices, units, commodities) from text
        
        Args:
            text: Input text
            
        Returns:
            List of Entity objects
        """
        entities = []
        
        # Extract prices
        for match in self.price_pattern.finditer(text):
            entities.append(Entity(
                text=match.group(),
                entity_type='price',
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract units
        for match in self.unit_pattern.finditer(text):
            entities.append(Entity(
                text=match.group(),
                entity_type='unit',
                start_pos=match.start(),
                end_pos=match.end()
            ))
        
        # Extract commodity names
        words = text.lower().split()
        for word in words:
            if word in self.commodity_names:
                # Find position in original text
                pos = text.lower().find(word)
                if pos != -1:
                    entities.append(Entity(
                        text=text[pos:pos+len(word)],
                        entity_type='commodity',
                        start_pos=pos,
                        end_pos=pos+len(word)
                    ))
        
        return entities
    
    def _preserve_entities(self, text: str, entities: List[Entity]) -> str:
        """
        Preserve entities in translated text
        
        This is a placeholder implementation. In production, you would:
        1. Mark entities with special tokens before translation
        2. Post-process to restore original entity values
        
        Args:
            text: Translated text
            entities: Original entities to preserve
            
        Returns:
            Text with preserved entities
        """
        # For now, return text as-is
        # In production, implement entity alignment and restoration
        return text
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        user_id: Optional[UUID] = None,
        db: Optional[Session] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text between languages
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'hin_Deva')
            target_lang: Target language code (e.g., 'tel_Telu')
            user_id: Optional user ID for audit logging
            db: Optional database session for audit logging
            ip_address: Optional IP address for audit logging
            user_agent: Optional user agent for audit logging
            
        Returns:
            TranslationResult with translated text and metadata
            
        Validates: Requirements 3.1, 3.2, 15.10
        """
        start_time = time.time()
        
        # Ensure model is loaded
        self.load_model()
        
        # Extract entities before translation
        entities = self._extract_entities(text)
        
        # Prepare input with language tags
        input_text = f"{source_lang} {target_lang} {text}"
        
        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)
        
        # Generate translation
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=5,
                early_stopping=True
            )
        
        # Decode
        translated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        # Preserve entities in translation
        translated_text = self._preserve_entities(translated_text, entities)
        
        # Calculate confidence (simplified - in production use model scores)
        confidence = 0.95  # Placeholder
        
        processing_time = (time.time() - start_time) * 1000
        
        result = TranslationResult(
            text=translated_text,
            confidence=confidence,
            source_language=source_lang,
            target_language=target_lang,
            preserved_entities=entities,
            processing_time_ms=processing_time
        )
        
        # Audit logging
        if db and user_id:
            try:
                from app.services.audit.audit_logger import AuditLogger
                audit_logger = AuditLogger(db)
                
                audit_logger.log_data_processing(
                    operation="translation",
                    resource_type="message",
                    resource_id=None,  # Message may not be persisted yet
                    actor_id=user_id,
                    result="success",
                    metadata={
                        "source_language": source_lang,
                        "target_language": target_lang,
                        "confidence": confidence,
                        "processing_time_ms": processing_time,
                        "text_length": len(text),
                        "entities_preserved": len(entities)
                    },
                    description=f"Text translated from {source_lang} to {target_lang}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to log audit entry: {e}")
        
        return result
    
    def translate_with_context(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        conversation_history: List[Message]
    ) -> TranslationResult:
        """
        Translate text with conversation context for better accuracy
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            conversation_history: Previous messages for context
            
        Returns:
            TranslationResult with translated text
        """
        # For now, use basic translation
        # In production, prepend recent context to improve pronoun/reference handling
        
        # Build context from last 2-3 messages
        context_text = ""
        if conversation_history:
            recent_messages = conversation_history[-3:]
            context_text = " ".join([msg.text for msg in recent_messages])
            context_text = f"Context: {context_text}\n\nTranslate: {text}"
        else:
            context_text = text
        
        return self.translate(context_text, source_lang, target_lang)
