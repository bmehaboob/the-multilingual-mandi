"""
LLM Service for generating negotiation suggestions.

This service handles loading and inference with quantized LLM models
(Llama 3.1 8B or Mistral 7B) for culturally-aware negotiation assistance.
"""

import logging
import os
from typing import Dict, List, Optional

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    GenerationConfig,
)

from .models import (
    CulturalContext,
    NegotiationState,
    NegotiationSuggestion,
    PriceAggregation,
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for LLM-based negotiation suggestion generation.
    
    Supports:
    - Llama 3.1 8B Instruct
    - Mistral 7B Instruct
    
    Uses 4-bit quantization for efficient inference.
    """
    
    # Supported models
    SUPPORTED_MODELS = {
        "llama-3.1-8b": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
    }
    
    def __init__(
        self,
        model_name: str = "llama-3.1-8b",
        device: Optional[str] = None,
        use_quantization: bool = True,
    ):
        """
        Initialize the LLM service.
        
        Args:
            model_name: Name of the model to use (llama-3.1-8b or mistral-7b)
            device: Device to run inference on (cuda, cpu, or None for auto)
            use_quantization: Whether to use 4-bit quantization
        """
        self.model_name = model_name
        self.use_quantization = use_quantization
        
        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Initializing LLM service with model: {model_name}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Quantization: {use_quantization}")
        
        # Model and tokenizer will be loaded lazily
        self.model = None
        self.tokenizer = None
        self.generation_config = None
        
        # Load prompt templates
        self.prompt_templates = self._load_prompt_templates()
    
    def _get_model_id(self) -> str:
        """Get the Hugging Face model ID for the selected model."""
        if self.model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {self.model_name}. "
                f"Supported models: {list(self.SUPPORTED_MODELS.keys())}"
            )
        return self.SUPPORTED_MODELS[self.model_name]
    
    def _load_model(self):
        """Load the LLM model and tokenizer."""
        if self.model is not None:
            return  # Already loaded
        
        model_id = self._get_model_id()
        logger.info(f"Loading model: {model_id}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                trust_remote_code=True,
            )
            
            # Set padding token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Configure quantization if enabled
            if self.use_quantization and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                )
            else:
                # Load without quantization (for CPU or when disabled)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
                )
                if self.device != "cuda":
                    self.model = self.model.to(self.device)
            
            # Configure generation parameters
            self.generation_config = GenerationConfig(
                max_new_tokens=200,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates for different negotiation scenarios."""
        return {
            "counter_offer": """You are a helpful negotiation assistant for farmers and traders in India. 
Your role is to suggest culturally appropriate counter-offers that maintain good relationships.

Context:
- Commodity: {commodity}
- Current Quote: ₹{current_price} per {unit}
- Market Average: ₹{market_average} per {unit}
- Relationship: {relationship_type}
- Conversation Tone: {sentiment}
- Language: {language}
- Region: {region}

Cultural Guidelines:
- Use honorifics: {honorifics}
- Negotiation style: {negotiation_style}
{festival_context}

Task: Suggest a polite counter-offer that:
1. Is within 15% of the market average (₹{min_price} - ₹{max_price})
2. Uses culturally appropriate language and honorifics
3. Maintains a {sentiment} tone
4. Avoids aggressive or confrontational phrasing

Provide your suggestion in this format:
SUGGESTED_PRICE: [price in rupees]
MESSAGE: [your negotiation message in English]
""",
        }
    
    def _build_prompt(
        self,
        negotiation_state: NegotiationState,
        market_data: PriceAggregation,
        cultural_context: CulturalContext,
    ) -> str:
        """
        Build a prompt for the LLM based on negotiation context.
        
        Args:
            negotiation_state: Current negotiation state
            market_data: Market price data
            cultural_context: Cultural context for the negotiation
        
        Returns:
            Formatted prompt string
        """
        template = self.prompt_templates["counter_offer"]
        
        # Calculate acceptable price range (within 15% of market average)
        market_avg = market_data.average_price
        min_price = market_avg * 0.85
        max_price = market_avg * 1.15
        
        # Format festival context if present
        festival_context = ""
        if cultural_context.festival_context:
            festival = cultural_context.festival_context
            festival_context = f"\n- Festival: {festival.festival_name} (typical adjustment: {festival.typical_price_adjustment:.1%})"
        
        # Format honorifics
        honorifics_str = ", ".join(cultural_context.honorifics[:3])  # Use top 3
        
        prompt = template.format(
            commodity=negotiation_state.commodity,
            current_price=negotiation_state.current_price,
            unit="kg",  # Default unit
            market_average=market_avg,
            relationship_type=cultural_context.relationship_terms[0] if cultural_context.relationship_terms else "trader",
            sentiment=negotiation_state.sentiment.value,
            language=cultural_context.language,
            region=cultural_context.region,
            honorifics=honorifics_str,
            negotiation_style=cultural_context.negotiation_style.value,
            festival_context=festival_context,
            min_price=min_price,
            max_price=max_price,
        )
        
        return prompt
    
    def _extract_suggestion(
        self,
        generated_text: str,
        market_average: float,
    ) -> NegotiationSuggestion:
        """
        Extract structured suggestion from LLM output.
        
        Args:
            generated_text: Raw text generated by LLM
            market_average: Market average price for validation
        
        Returns:
            Structured negotiation suggestion
        """
        # Parse the generated text
        lines = generated_text.strip().split("\n")
        
        suggested_price = None
        message = ""
        
        for line in lines:
            if line.startswith("SUGGESTED_PRICE:"):
                price_str = line.replace("SUGGESTED_PRICE:", "").strip()
                # Extract numeric value
                price_str = "".join(c for c in price_str if c.isdigit() or c == ".")
                try:
                    suggested_price = float(price_str)
                except ValueError:
                    logger.warning(f"Could not parse price from: {line}")
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
        
        # Validate and adjust suggested price
        price_extracted = suggested_price is not None
        if suggested_price is None:
            # Fallback: suggest market average
            suggested_price = market_average
            logger.warning("Could not extract price from LLM output, using market average")
        
        # Ensure price is within 15% of market average
        min_price = market_average * 0.85
        max_price = market_average * 1.15
        suggested_price = max(min_price, min(max_price, suggested_price))
        
        # Calculate confidence based on how well-formed the output is
        if message and price_extracted:
            confidence = 0.8
        elif message or price_extracted:
            confidence = 0.6
        else:
            confidence = 0.5
        
        rationale = f"Based on market average of ₹{market_average:.2f}, suggesting ₹{suggested_price:.2f}"
        
        return NegotiationSuggestion(
            suggested_price=suggested_price,
            message=message or "Consider this counter-offer based on current market prices.",
            rationale=rationale,
            confidence=confidence,
        )
    
    def generate_counter_offer(
        self,
        negotiation_state: NegotiationState,
        market_data: PriceAggregation,
        cultural_context: CulturalContext,
    ) -> NegotiationSuggestion:
        """
        Generate a culturally-appropriate counter-offer suggestion.
        
        Args:
            negotiation_state: Current state of the negotiation
            market_data: Market price data
            cultural_context: Cultural context for the negotiation
        
        Returns:
            Negotiation suggestion with price and message
        
        Requirements: 8.1, 8.2, 8.3, 8.4, 9.1
        """
        # Ensure model is loaded
        self._load_model()
        
        # Build prompt
        prompt = self._build_prompt(negotiation_state, market_data, cultural_context)
        
        logger.debug(f"Generated prompt: {prompt[:200]}...")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=1024,
            )
            
            # Move to device
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    generation_config=self.generation_config,
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
            )
            
            # Remove the prompt from the output
            if prompt in generated_text:
                generated_text = generated_text.replace(prompt, "").strip()
            
            logger.debug(f"Generated text: {generated_text}")
            
            # Extract structured suggestion
            suggestion = self._extract_suggestion(
                generated_text,
                market_data.average_price,
            )
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating counter-offer: {e}")
            # Fallback: return a simple suggestion based on market average
            return NegotiationSuggestion(
                suggested_price=market_data.average_price,
                message="Consider offering the market average price.",
                rationale=f"Fallback suggestion due to generation error: {str(e)}",
                confidence=0.3,
            )
    
    def unload_model(self):
        """Unload the model from memory."""
        if self.model is not None:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Model unloaded from memory")
