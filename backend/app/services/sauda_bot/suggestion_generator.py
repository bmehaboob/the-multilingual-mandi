"""
Suggestion Generator for Sauda Bot.

Orchestrates LLM service, cultural context engine, and negotiation context analyzer
to generate culturally-appropriate negotiation suggestions.

Requirements: 8.1, 8.2, 8.3, 8.4, 9.1, 9.5
"""

import logging
import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .cultural_context_engine import CulturalContextEngine
from .llm_service import LLMService
from .models import (
    Message,
    NegotiationState,
    NegotiationSuggestion,
    PriceAggregation,
    RelationshipContext,
)
from .negotiation_context_analyzer import NegotiationContextAnalyzer

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """
    Generates culturally-appropriate negotiation suggestions using LLM.
    
    Orchestrates:
    - NegotiationContextAnalyzer: Extracts negotiation state and sentiment
    - CulturalContextEngine: Provides cultural norms and honorifics
    - LLMService: Generates suggestions using language model
    
    Ensures:
    - Counter-offers within 15% of market average (Requirement 8.2)
    - Culturally appropriate honorifics and relationship terms (Requirement 9.1)
    - No aggressive language (Requirement 9.5)
    """
    
    # Aggressive language patterns to filter out
    AGGRESSIVE_PATTERNS = [
        r'\b(stupid|idiot|fool|cheat|liar|scam|fraud)\b',
        r'\b(never|impossible|ridiculous|absurd|outrageous)\b',
        r'\b(must|demand|insist|force|require)\b',
        r'\b(threat|warning|else|or else)\b',
        # Hindi aggressive terms
        r'\b(बेवकूफ|मूर्ख|धोखा|झूठा)\b',
        # Telugu aggressive terms
        r'\b(మూర్ఖుడు|మోసం|అబద్ధం)\b',
        # Tamil aggressive terms
        r'\b(முட்டாள்|ஏமாற்று|பொய்)\b',
    ]
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        cultural_engine: Optional[CulturalContextEngine] = None,
        context_analyzer: Optional[NegotiationContextAnalyzer] = None,
    ):
        """
        Initialize the suggestion generator.
        
        Args:
            llm_service: Optional LLM service instance (creates new if None)
            cultural_engine: Optional cultural context engine (creates new if None)
            context_analyzer: Optional context analyzer (creates new if None)
        """
        self.llm_service = llm_service or LLMService()
        self.cultural_engine = cultural_engine or CulturalContextEngine()
        self.context_analyzer = context_analyzer or NegotiationContextAnalyzer()
        
        logger.info("SuggestionGenerator initialized")
    
    def _validate_price_bounds(
        self,
        suggested_price: float,
        market_average: float,
    ) -> float:
        """
        Ensures suggested price is within 15% of market average.
        
        Args:
            suggested_price: Price suggested by LLM
            market_average: Market average price
            
        Returns:
            Validated price within bounds
            
        Requirement 8.2: Counter-offers within 15% of market average
        """
        min_price = market_average * 0.85
        max_price = market_average * 1.15
        
        # Clamp price to valid range
        validated_price = max(min_price, min(max_price, suggested_price))
        
        if validated_price != suggested_price:
            logger.info(
                f"Adjusted price from {suggested_price:.2f} to {validated_price:.2f} "
                f"to stay within 15% of market average {market_average:.2f}"
            )
        
        return validated_price
    
    def _filter_aggressive_language(self, message: str) -> str:
        """
        Filters out aggressive or confrontational language.
        
        Args:
            message: Message text to filter
            
        Returns:
            Filtered message with aggressive terms removed/replaced
            
        Requirement 9.5: Avoid aggressive language
        """
        filtered_message = message
        
        # Check for aggressive patterns
        for pattern in self.AGGRESSIVE_PATTERNS:
            if re.search(pattern, filtered_message, re.IGNORECASE):
                logger.warning(f"Detected aggressive language pattern: {pattern}")
                # Replace aggressive terms with neutral alternatives
                filtered_message = re.sub(
                    pattern,
                    "[polite term]",
                    filtered_message,
                    flags=re.IGNORECASE
                )
        
        # If message was heavily filtered, replace with safe default
        if "[polite term]" in filtered_message:
            logger.warning("Message contained aggressive language, using safe default")
            filtered_message = (
                "I would like to discuss a fair price that works for both of us. "
                "Could we consider a price closer to the market average?"
            )
        
        return filtered_message
    
    def _ensure_honorifics(
        self,
        message: str,
        honorifics: List[str],
        relationship_terms: List[str],
    ) -> str:
        """
        Ensures message includes culturally appropriate honorifics.
        
        Args:
            message: Message text
            honorifics: List of appropriate honorifics
            relationship_terms: List of appropriate relationship terms
            
        Returns:
            Message with honorifics included
            
        Requirement 9.1: Include honorifics and relationship terms
        """
        # Check if message already contains honorifics
        has_honorific = any(
            honorific.lower() in message.lower()
            for honorific in honorifics
        )
        
        has_relationship_term = any(
            term.lower() in message.lower()
            for term in relationship_terms
        )
        
        # If missing both, prepend an honorific
        if not has_honorific and not has_relationship_term and honorifics:
            # Use the first (most appropriate) honorific
            primary_honorific = honorifics[0]
            message = f"{primary_honorific}, {message}"
            logger.info(f"Added honorific '{primary_honorific}' to message")
        
        return message
    
    def generate_counter_offer(
        self,
        conversation: List[Message],
        market_data: PriceAggregation,
        user_id: UUID,
        other_party_id: UUID,
        language: str,
        region: str,
        transaction_history: Optional[List[dict]] = None,
    ) -> NegotiationSuggestion:
        """
        Generates a culturally-appropriate counter-offer suggestion.
        
        This is the main entry point for generating negotiation suggestions.
        
        Args:
            conversation: List of messages in the conversation
            market_data: Market price aggregation data
            user_id: ID of the user requesting suggestion
            other_party_id: ID of the other party
            language: Language for the suggestion
            region: Region/state for cultural context
            transaction_history: Optional transaction history for relationship analysis
            
        Returns:
            NegotiationSuggestion with validated price and culturally-appropriate message
            
        Requirements:
        - 8.1: Analyze quote and market average
        - 8.2: Suggest price within 15% of market average
        - 8.3: Generate culturally appropriate suggestions
        - 8.4: Adapt tone based on relationship
        - 9.1: Include honorifics and relationship terms
        - 9.5: Avoid aggressive language
        """
        logger.info(
            f"Generating counter-offer suggestion for {language} in {region}"
        )
        
        # Step 1: Extract negotiation state (Requirement 8.1)
        negotiation_state = self.context_analyzer.extract_negotiation_state(
            conversation
        )
        logger.info(
            f"Negotiation state: commodity={negotiation_state.commodity}, "
            f"current_price={negotiation_state.current_price:.2f}, "
            f"sentiment={negotiation_state.sentiment.value}"
        )
        
        # Step 2: Analyze relationship (Requirement 8.4)
        relationship = self.context_analyzer.analyze_relationship(
            user_id,
            other_party_id,
            transaction_history,
        )
        logger.info(
            f"Relationship: type={relationship.relationship_type.value}, "
            f"transaction_count={relationship.transaction_count}"
        )
        
        # Step 3: Build cultural context (Requirements 9.1, 8.3)
        cultural_context = self.cultural_engine.build_cultural_context(
            language=language,
            region=region,
            relationship=relationship,
            date=datetime.now(),
            commodity=negotiation_state.commodity,
        )
        logger.info(
            f"Cultural context: style={cultural_context.negotiation_style.value}, "
            f"honorifics={cultural_context.honorifics[:2]}"
        )
        
        # Step 4: Generate suggestion using LLM
        suggestion = self.llm_service.generate_counter_offer(
            negotiation_state=negotiation_state,
            market_data=market_data,
            cultural_context=cultural_context,
        )
        
        # Step 5: Validate price bounds (Requirement 8.2)
        validated_price = self._validate_price_bounds(
            suggestion.suggested_price,
            market_data.average_price,
        )
        suggestion.suggested_price = validated_price
        
        # Step 6: Filter aggressive language (Requirement 9.5)
        filtered_message = self._filter_aggressive_language(suggestion.message)
        
        # Step 7: Ensure honorifics are present (Requirement 9.1)
        final_message = self._ensure_honorifics(
            filtered_message,
            cultural_context.honorifics,
            cultural_context.relationship_terms,
        )
        suggestion.message = final_message
        
        logger.info(
            f"Generated suggestion: price={suggestion.suggested_price:.2f}, "
            f"confidence={suggestion.confidence:.2f}"
        )
        
        return suggestion
    
    def generate_counter_offer_with_historical_fallback(
        self,
        conversation: List[Message],
        market_data: Optional[PriceAggregation],
        historical_prices: List[float],
        user_id: UUID,
        other_party_id: UUID,
        language: str,
        region: str,
        transaction_history: Optional[List[dict]] = None,
    ) -> NegotiationSuggestion:
        """
        Generates counter-offer with fallback to historical data.
        
        If market_data is unavailable, uses historical prices from past 7 days.
        
        Args:
            conversation: List of messages in the conversation
            market_data: Market price data (None if unavailable)
            historical_prices: List of historical prices from past 7 days
            user_id: ID of the user requesting suggestion
            other_party_id: ID of the other party
            language: Language for the suggestion
            region: Region/state for cultural context
            transaction_history: Optional transaction history
            
        Returns:
            NegotiationSuggestion
            
        Requirement 8.5: Use historical data when market average unavailable
        """
        # If market data is available, use normal flow
        if market_data is not None:
            return self.generate_counter_offer(
                conversation=conversation,
                market_data=market_data,
                user_id=user_id,
                other_party_id=other_party_id,
                language=language,
                region=region,
                transaction_history=transaction_history,
            )
        
        # Fallback: Create synthetic market data from historical prices
        logger.warning(
            "Market data unavailable, using historical prices as fallback"
        )
        
        if not historical_prices:
            raise ValueError(
                "Cannot generate suggestion: no market data or historical prices available"
            )
        
        # Calculate statistics from historical prices
        avg_price = sum(historical_prices) / len(historical_prices)
        min_price = min(historical_prices)
        max_price = max(historical_prices)
        
        # Create synthetic market data
        synthetic_market_data = PriceAggregation(
            commodity="unknown",
            min_price=min_price,
            max_price=max_price,
            average_price=avg_price,
            median_price=avg_price,  # Approximation
            std_dev=0.0,  # Not calculated
            sample_size=len(historical_prices),
            timestamp=datetime.now(),
        )
        
        logger.info(
            f"Using historical average: {avg_price:.2f} "
            f"(from {len(historical_prices)} prices)"
        )
        
        # Generate suggestion with synthetic data
        return self.generate_counter_offer(
            conversation=conversation,
            market_data=synthetic_market_data,
            user_id=user_id,
            other_party_id=other_party_id,
            language=language,
            region=region,
            transaction_history=transaction_history,
        )
    
    def unload_model(self):
        """Unload LLM model from memory."""
        self.llm_service.unload_model()
