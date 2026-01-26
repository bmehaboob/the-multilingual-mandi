"""
Negotiation Context Analyzer for Sauda Bot.

Analyzes conversation context to extract negotiation state, relationship context,
and sentiment for culturally-aware negotiation assistance.

Requirements: 9.2
"""

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .models import (
    Message,
    NegotiationState,
    RelationshipContext,
    RelationshipType,
    SentimentType,
)


class NegotiationContextAnalyzer:
    """
    Analyzes conversation context for negotiation.
    
    Extracts:
    - Negotiation state (commodity, quotes, sentiment)
    - User relationship (new vs. repeat customer)
    - Sentiment detection (friendly, formal, tense)
    """
    
    def __init__(self):
        """Initialize the negotiation context analyzer."""
        # Patterns for extracting prices from text
        self.price_patterns = [
            r'₹\s*(\d+(?:\.\d+)?)',  # ₹100 or ₹100.50
            r'Rs\.?\s*(\d+(?:\.\d+)?)',  # Rs.100 or Rs 100
            r'rupees?\s*(\d+(?:\.\d+)?)',  # rupees 100
            r'(\d+(?:\.\d+)?)\s*(?:rupees?|rs|₹)',  # 100 rupees
            r'(\d+(?:\.\d+)?)\s*per\s*kg',  # 100 per kg
        ]
        
        # Keywords for sentiment detection
        self.friendly_keywords = [
            'friend', 'brother', 'sister', 'please', 'thank', 'appreciate',
            'भाई', 'दोस्त', 'धन्यवाद', 'कृपया',  # Hindi
            'అన్నయ్య', 'తమ్ముడు', 'ధన్యవాదాలు',  # Telugu
            'நண்பர்', 'நன்றி',  # Tamil
        ]
        
        self.formal_keywords = [
            'sir', 'madam', 'respected', 'honorable', 'business', 'deal',
            'साहब', 'महोदय', 'जी',  # Hindi
            'గారు', 'మాన్యులు',  # Telugu
            'அவர்கள்', 'மதிப்பிற்குரிய',  # Tamil
        ]
        
        self.tense_keywords = [
            'no', 'cannot', 'impossible', 'too much', 'too high', 'unfair',
            'नहीं', 'असंभव', 'बहुत ज्यादा',  # Hindi
            'కాదు', 'అసాధ్యం', 'చాలా ఎక్కువ',  # Telugu
            'இல்லை', 'முடியாது',  # Tamil
        ]
        
        # Common commodity names in multiple languages (including plural forms)
        self.commodity_patterns = [
            # English (singular and plural)
            r'\b(tomato(?:es)?|onion(?:s)?|potato(?:es)?|rice|wheat|corn|cotton|sugarcane|banana(?:s)?|mango(?:es)?|apple(?:s)?|orange(?:s)?)\b',
            # Hindi
            r'\b(टमाटर|प्याज|आलू|चावल|गेहूं|मक्का|कपास|गन्ना|केला|आम|सेब|संतरा)\b',
            # Telugu
            r'\b(టమాటో|ఉల్లిపాయ|బంగాళాదుంప|బియ్యం|గోధుమ|మొక్కజొన్న|పత్తి|చెరకు|అరటి|మామిడి|ఆపిల్|నారింజ)\b',
            # Tamil
            r'\b(தக்காளி|வெங்காயம்|உருளைக்கிழங்கு|அரிசி|கோதுமை|சோளம்|பருத்தி|கரும்பு|வாழை|மாம்பழம்|ஆப்பிள்|ஆரஞ்சு)\b',
        ]
    
    def extract_negotiation_state(
        self,
        conversation: List[Message]
    ) -> NegotiationState:
        """
        Extracts negotiation state from conversation.
        
        Args:
            conversation: List of messages in the conversation
            
        Returns:
            NegotiationState with commodity, quotes, and sentiment
        """
        if not conversation:
            raise ValueError("Conversation cannot be empty")
        
        # Extract commodity
        commodity = self._extract_commodity(conversation)
        
        # Extract all price quotes
        all_quotes = self._extract_quotes(conversation)
        
        # Determine initial quote and counter offers
        initial_quote = all_quotes[0] if all_quotes else 0.0
        counter_offers = all_quotes[1:] if len(all_quotes) > 1 else []
        current_price = all_quotes[-1] if all_quotes else 0.0
        
        # Detect sentiment
        sentiment = self.detect_sentiment(conversation)
        
        return NegotiationState(
            commodity=commodity,
            initial_quote=initial_quote,
            counter_offers=counter_offers,
            current_price=current_price,
            sentiment=sentiment,
            messages=conversation,
        )
    
    def _extract_commodity(self, conversation: List[Message]) -> str:
        """
        Extracts commodity name from conversation.
        
        Args:
            conversation: List of messages
            
        Returns:
            Commodity name or "unknown" if not found
        """
        # Combine all message texts
        combined_text = " ".join(msg.text.lower() for msg in conversation)
        
        # Try each commodity pattern
        for pattern in self.commodity_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _extract_quotes(self, conversation: List[Message]) -> List[float]:
        """
        Extracts all price quotes from conversation.
        
        Args:
            conversation: List of messages
            
        Returns:
            List of prices in chronological order
        """
        quotes = []
        
        for message in conversation:
            # Track which prices we've already found in this message to avoid duplicates
            found_prices = set()
            
            # Try each price pattern
            for pattern in self.price_patterns:
                matches = re.finditer(pattern, message.text, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match.group(1))
                        # Filter out unrealistic prices (e.g., years, quantities)
                        if 1.0 <= price <= 10000.0 and price not in found_prices:
                            quotes.append(price)
                            found_prices.add(price)
                    except (ValueError, IndexError):
                        continue
        
        return quotes
    
    def detect_sentiment(self, messages: List[Message]) -> SentimentType:
        """
        Analyzes tone of conversation: friendly, formal, or tense.
        
        Uses simple rule-based sentiment detection based on keywords.
        
        Args:
            messages: List of messages to analyze
            
        Returns:
            SentimentType (FRIENDLY, FORMAL, TENSE, or NEUTRAL)
        """
        if not messages:
            return SentimentType.NEUTRAL
        
        # Combine all message texts
        combined_text = " ".join(msg.text.lower() for msg in messages)
        
        # Count keyword matches
        friendly_count = sum(
            1 for keyword in self.friendly_keywords
            if keyword.lower() in combined_text
        )
        
        formal_count = sum(
            1 for keyword in self.formal_keywords
            if keyword.lower() in combined_text
        )
        
        tense_count = sum(
            1 for keyword in self.tense_keywords
            if keyword.lower() in combined_text
        )
        
        # Determine sentiment based on highest count
        max_count = max(friendly_count, formal_count, tense_count)
        
        if max_count == 0:
            return SentimentType.NEUTRAL
        
        if friendly_count == max_count:
            return SentimentType.FRIENDLY
        elif formal_count == max_count:
            return SentimentType.FORMAL
        else:
            return SentimentType.TENSE
    
    def analyze_relationship(
        self,
        user_id: UUID,
        other_party_id: UUID,
        transaction_history: Optional[List[dict]] = None
    ) -> RelationshipContext:
        """
        Determines relationship between trading parties.
        
        Args:
            user_id: ID of the current user
            other_party_id: ID of the other party
            transaction_history: Optional list of past transactions
            
        Returns:
            RelationshipContext with relationship type and transaction count
        """
        if transaction_history is None:
            transaction_history = []
        
        # Filter transactions between these two parties
        relevant_transactions = [
            tx for tx in transaction_history
            if (
                (tx.get('buyer_id') == user_id and tx.get('seller_id') == other_party_id)
                or (tx.get('buyer_id') == other_party_id and tx.get('seller_id') == user_id)
            )
        ]
        
        transaction_count = len(relevant_transactions)
        
        # Determine relationship type
        if transaction_count == 0:
            relationship_type = RelationshipType.NEW_CUSTOMER
        elif transaction_count < 5:
            relationship_type = RelationshipType.REPEAT_CUSTOMER
        else:
            relationship_type = RelationshipType.FREQUENT_PARTNER
        
        # Get last transaction date
        last_transaction_date = None
        if relevant_transactions:
            # Sort by date and get the most recent
            sorted_transactions = sorted(
                relevant_transactions,
                key=lambda tx: tx.get('completed_at', datetime.min),
                reverse=True
            )
            last_transaction_date = sorted_transactions[0].get('completed_at')
        
        return RelationshipContext(
            relationship_type=relationship_type,
            transaction_count=transaction_count,
            last_transaction_date=last_transaction_date,
        )
