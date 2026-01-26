"""
Cultural Context Engine for Sauda Bot.

Manages cultural norms, honorifics, festival calendars, and regional negotiation
styles for culturally-aware negotiation assistance.

Requirements: 9.1, 9.7, 9.8
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .models import (
    CulturalContext,
    FestivalContext,
    NegotiationStyle,
    RelationshipContext,
    RelationshipType,
)


class CulturalContextEngine:
    """
    Manages cultural norms and regional preferences.
    
    Provides:
    - Regional norms and honorifics for all languages
    - Festival calendar with pricing adjustments
    - Regional negotiation style preferences
    """
    
    def __init__(self):
        """Initialize the cultural context engine."""
        self.regional_norms = self._load_regional_norms()
        self.festival_calendar = self._load_festival_calendar()
    
    def _load_regional_norms(self) -> Dict[str, Dict]:
        """
        Loads regional norms including honorifics and negotiation styles.
        
        Returns:
            Dictionary mapping region/language to cultural norms
        """
        return {
            # Hindi-speaking regions (North India)
            "hindi": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["जी", "साहब", "भाई साहब"],
                    RelationshipType.REPEAT_CUSTOMER: ["भाई", "दोस्त", "जी"],
                    RelationshipType.FREQUENT_PARTNER: ["भाई", "मित्र", "यार"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["आप", "आपका"],
                    RelationshipType.REPEAT_CUSTOMER: ["आप", "तुम्हारा"],
                    RelationshipType.FREQUENT_PARTNER: ["तुम", "तेरा"],
                },
                "negotiation_style": NegotiationStyle.RELATIONSHIP_FOCUSED,
                "regions": ["Delhi", "Uttar Pradesh", "Madhya Pradesh", "Rajasthan", "Haryana", "Himachal Pradesh"],
            },
            
            # Telugu-speaking regions (Andhra Pradesh, Telangana)
            "telugu": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["గారు", "అన్నయ్య", "దొరగారు"],
                    RelationshipType.REPEAT_CUSTOMER: ["అన్నయ్య", "తమ్ముడు", "గారు"],
                    RelationshipType.FREQUENT_PARTNER: ["అన్నయ్య", "బావ", "మిత్రమా"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["మీరు", "మీ"],
                    RelationshipType.REPEAT_CUSTOMER: ["మీరు", "నీవు"],
                    RelationshipType.FREQUENT_PARTNER: ["నీవు", "నీ"],
                },
                "negotiation_style": NegotiationStyle.RELATIONSHIP_FOCUSED,
                "regions": ["Andhra Pradesh", "Telangana"],
            },
            
            # Tamil-speaking regions (Tamil Nadu)
            "tamil": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["அவர்கள்", "ஐயா", "அண்ணா"],
                    RelationshipType.REPEAT_CUSTOMER: ["அண்ணா", "தம்பி", "நண்பா"],
                    RelationshipType.FREQUENT_PARTNER: ["நண்பா", "மச்சி", "தோழா"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["நீங்கள்", "உங்கள்"],
                    RelationshipType.REPEAT_CUSTOMER: ["நீங்கள்", "உன்"],
                    RelationshipType.FREQUENT_PARTNER: ["நீ", "உன்"],
                },
                "negotiation_style": NegotiationStyle.DIRECT,
                "regions": ["Tamil Nadu", "Puducherry"],
            },
            
            # Kannada-speaking regions (Karnataka)
            "kannada": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["ಅವರೇ", "ಸರ್", "ಅಣ್ಣ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ಅಣ್ಣ", "ತಮ್ಮ", "ಗೆಳೆಯ"],
                    RelationshipType.FREQUENT_PARTNER: ["ಗೆಳೆಯ", "ಮಿತ್ರ", "ಸ್ನೇಹಿತ"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["ನೀವು", "ನಿಮ್ಮ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ನೀವು", "ನಿನ್ನ"],
                    RelationshipType.FREQUENT_PARTNER: ["ನೀನು", "ನಿನ್ನ"],
                },
                "negotiation_style": NegotiationStyle.BUSINESS_FOCUSED,
                "regions": ["Karnataka"],
            },
            
            # Marathi-speaking regions (Maharashtra)
            "marathi": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["साहेब", "दादा", "भाऊ"],
                    RelationshipType.REPEAT_CUSTOMER: ["दादा", "भाऊ", "मित्रा"],
                    RelationshipType.FREQUENT_PARTNER: ["मित्रा", "भाऊ", "बंधू"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["तुम्ही", "तुमचा"],
                    RelationshipType.REPEAT_CUSTOMER: ["तुम्ही", "तुझा"],
                    RelationshipType.FREQUENT_PARTNER: ["तू", "तुझा"],
                },
                "negotiation_style": NegotiationStyle.BUSINESS_FOCUSED,
                "regions": ["Maharashtra", "Goa"],
            },
            
            # Bengali-speaking regions (West Bengal)
            "bengali": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["বাবু", "দাদা", "ভাই"],
                    RelationshipType.REPEAT_CUSTOMER: ["দাদা", "ভাই", "বন্ধু"],
                    RelationshipType.FREQUENT_PARTNER: ["বন্ধু", "ভাই", "মিত্র"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["আপনি", "আপনার"],
                    RelationshipType.REPEAT_CUSTOMER: ["আপনি", "তোমার"],
                    RelationshipType.FREQUENT_PARTNER: ["তুমি", "তোমার"],
                },
                "negotiation_style": NegotiationStyle.RELATIONSHIP_FOCUSED,
                "regions": ["West Bengal", "Tripura"],
            },
            
            # Gujarati-speaking regions (Gujarat)
            "gujarati": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["સાહેબ", "ભાઈ", "શેઠ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ભાઈ", "મિત્ર", "સાથી"],
                    RelationshipType.FREQUENT_PARTNER: ["મિત્ર", "ભાઈ", "દોસ્ત"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["તમે", "તમારું"],
                    RelationshipType.REPEAT_CUSTOMER: ["તમે", "તારું"],
                    RelationshipType.FREQUENT_PARTNER: ["તું", "તારું"],
                },
                "negotiation_style": NegotiationStyle.BUSINESS_FOCUSED,
                "regions": ["Gujarat", "Dadra and Nagar Haveli", "Daman and Diu"],
            },
            
            # Punjabi-speaking regions (Punjab)
            "punjabi": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["ਜੀ", "ਸਾਹਿਬ", "ਭਰਾ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ਭਰਾ", "ਯਾਰ", "ਮਿੱਤਰ"],
                    RelationshipType.FREQUENT_PARTNER: ["ਯਾਰ", "ਮਿੱਤਰ", "ਦੋਸਤ"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["ਤੁਸੀਂ", "ਤੁਹਾਡਾ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ਤੁਸੀਂ", "ਤੇਰਾ"],
                    RelationshipType.FREQUENT_PARTNER: ["ਤੂੰ", "ਤੇਰਾ"],
                },
                "negotiation_style": NegotiationStyle.DIRECT,
                "regions": ["Punjab", "Chandigarh"],
            },
            
            # Malayalam-speaking regions (Kerala)
            "malayalam": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["സാർ", "ചേട്ടാ", "സാഹിബ്"],
                    RelationshipType.REPEAT_CUSTOMER: ["ചേട്ടാ", "സുഹൃത്തേ", "സഖാവേ"],
                    RelationshipType.FREQUENT_PARTNER: ["സുഹൃത്തേ", "കൂട്ടുകാരാ", "സഖാവേ"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["താങ്കൾ", "താങ്കളുടെ"],
                    RelationshipType.REPEAT_CUSTOMER: ["നിങ്ങൾ", "നിങ്ങളുടെ"],
                    RelationshipType.FREQUENT_PARTNER: ["നീ", "നിന്റെ"],
                },
                "negotiation_style": NegotiationStyle.INDIRECT,
                "regions": ["Kerala", "Lakshadweep"],
            },
            
            # Odia-speaking regions (Odisha)
            "odia": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["ବାବୁ", "ଭାଇ", "ସାହେବ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ଭାଇ", "ବନ୍ଧୁ", "ମିତ୍ର"],
                    RelationshipType.FREQUENT_PARTNER: ["ବନ୍ଧୁ", "ମିତ୍ର", "ସାଥୀ"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["ଆପଣ", "ଆପଣଙ୍କ"],
                    RelationshipType.REPEAT_CUSTOMER: ["ଆପଣ", "ତୁମର"],
                    RelationshipType.FREQUENT_PARTNER: ["ତୁମେ", "ତୁମର"],
                },
                "negotiation_style": NegotiationStyle.RELATIONSHIP_FOCUSED,
                "regions": ["Odisha"],
            },
            
            # Assamese-speaking regions (Assam)
            "assamese": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["দেউতা", "ভাই", "চাহাব"],
                    RelationshipType.REPEAT_CUSTOMER: ["ভাই", "বন্ধু", "সাথী"],
                    RelationshipType.FREQUENT_PARTNER: ["বন্ধু", "সাথী", "মিত্ৰ"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["আপুনি", "আপোনাৰ"],
                    RelationshipType.REPEAT_CUSTOMER: ["আপুনি", "তোমাৰ"],
                    RelationshipType.FREQUENT_PARTNER: ["তুমি", "তোমাৰ"],
                },
                "negotiation_style": NegotiationStyle.RELATIONSHIP_FOCUSED,
                "regions": ["Assam"],
            },
            
            # Urdu-speaking regions
            "urdu": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["جناب", "صاحب", "بھائی"],
                    RelationshipType.REPEAT_CUSTOMER: ["بھائی", "دوست", "یار"],
                    RelationshipType.FREQUENT_PARTNER: ["یار", "دوست", "ساتھی"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["آپ", "آپ کا"],
                    RelationshipType.REPEAT_CUSTOMER: ["آپ", "تمہارا"],
                    RelationshipType.FREQUENT_PARTNER: ["تم", "تیرا"],
                },
                "negotiation_style": NegotiationStyle.RELATIONSHIP_FOCUSED,
                "regions": ["Jammu and Kashmir", "Telangana", "Bihar"],
            },
            
            # English (for pan-India business communication)
            "english": {
                "honorifics": {
                    RelationshipType.NEW_CUSTOMER: ["Sir", "Madam", "Mr.", "Ms."],
                    RelationshipType.REPEAT_CUSTOMER: ["Sir", "Friend", "Brother"],
                    RelationshipType.FREQUENT_PARTNER: ["Friend", "Brother", "Partner"],
                },
                "relationship_terms": {
                    RelationshipType.NEW_CUSTOMER: ["you", "your"],
                    RelationshipType.REPEAT_CUSTOMER: ["you", "your"],
                    RelationshipType.FREQUENT_PARTNER: ["you", "your"],
                },
                "negotiation_style": NegotiationStyle.BUSINESS_FOCUSED,
                "regions": ["Pan-India"],
            },
        }
    
    def _load_festival_calendar(self) -> List[Dict]:
        """
        Loads festival calendar with pricing adjustments.
        
        Returns:
            List of festivals with dates and price adjustments
        """
        # Note: These are approximate dates. In production, use a proper calendar library
        # that accounts for lunar calendar variations
        return [
            # National festivals
            {
                "name": "Diwali",
                "month": 10,  # October-November (varies)
                "day_range": (15, 30),
                "regions": ["Pan-India"],
                "price_adjustment": 1.15,  # 15% increase
                "affected_commodities": ["all"],
            },
            {
                "name": "Holi",
                "month": 3,  # March (varies)
                "day_range": (1, 15),
                "regions": ["Pan-India"],
                "price_adjustment": 1.10,  # 10% increase
                "affected_commodities": ["all"],
            },
            
            # Regional festivals
            {
                "name": "Pongal",
                "month": 1,  # January 14-17
                "day_range": (14, 17),
                "regions": ["Tamil Nadu", "Puducherry"],
                "price_adjustment": 1.20,  # 20% increase
                "affected_commodities": ["rice", "sugarcane", "turmeric"],
            },
            {
                "name": "Onam",
                "month": 8,  # August-September (varies)
                "day_range": (15, 30),
                "regions": ["Kerala"],
                "price_adjustment": 1.18,  # 18% increase
                "affected_commodities": ["banana", "coconut", "vegetables"],
            },
            {
                "name": "Durga Puja",
                "month": 10,  # October (varies)
                "day_range": (1, 15),
                "regions": ["West Bengal", "Assam", "Tripura"],
                "price_adjustment": 1.20,  # 20% increase
                "affected_commodities": ["all"],
            },
            {
                "name": "Ganesh Chaturthi",
                "month": 9,  # September (varies)
                "day_range": (1, 15),
                "regions": ["Maharashtra", "Karnataka", "Goa"],
                "price_adjustment": 1.12,  # 12% increase
                "affected_commodities": ["all"],
            },
            {
                "name": "Ugadi",
                "month": 3,  # March-April (varies)
                "day_range": (15, 30),
                "regions": ["Karnataka", "Andhra Pradesh", "Telangana"],
                "price_adjustment": 1.15,  # 15% increase
                "affected_commodities": ["mango", "neem", "jaggery"],
            },
            {
                "name": "Baisakhi",
                "month": 4,  # April 13-14
                "day_range": (13, 14),
                "regions": ["Punjab", "Haryana"],
                "price_adjustment": 1.10,  # 10% increase
                "affected_commodities": ["wheat", "rice"],
            },
            {
                "name": "Eid al-Fitr",
                "month": None,  # Varies based on lunar calendar
                "day_range": None,
                "regions": ["Pan-India"],
                "price_adjustment": 1.12,  # 12% increase
                "affected_commodities": ["all"],
            },
            {
                "name": "Eid al-Adha",
                "month": None,  # Varies based on lunar calendar
                "day_range": None,
                "regions": ["Pan-India"],
                "price_adjustment": 1.10,  # 10% increase
                "affected_commodities": ["all"],
            },
            
            # Harvest seasons (affect pricing)
            {
                "name": "Rabi Harvest",
                "month": 4,  # April-May
                "day_range": (1, 31),
                "regions": ["Pan-India"],
                "price_adjustment": 0.90,  # 10% decrease (abundant supply)
                "affected_commodities": ["wheat", "barley", "mustard", "chickpea"],
            },
            {
                "name": "Kharif Harvest",
                "month": 10,  # October-November
                "day_range": (1, 31),
                "regions": ["Pan-India"],
                "price_adjustment": 0.92,  # 8% decrease (abundant supply)
                "affected_commodities": ["rice", "cotton", "soybean", "sugarcane"],
            },
        ]
    
    def get_honorifics(
        self,
        language: str,
        relationship: RelationshipContext
    ) -> List[str]:
        """
        Returns appropriate honorifics for language and relationship.
        
        Args:
            language: Language code (e.g., "hindi", "telugu")
            relationship: Relationship context between parties
            
        Returns:
            List of appropriate honorifics
        """
        language_lower = language.lower()
        
        # Default to English if language not found
        if language_lower not in self.regional_norms:
            language_lower = "english"
        
        norms = self.regional_norms[language_lower]
        honorifics = norms["honorifics"].get(
            relationship.relationship_type,
            norms["honorifics"][RelationshipType.NEW_CUSTOMER]
        )
        
        return honorifics
    
    def get_relationship_terms(
        self,
        language: str,
        relationship: RelationshipContext
    ) -> List[str]:
        """
        Returns appropriate relationship terms for language and relationship.
        
        Args:
            language: Language code (e.g., "hindi", "telugu")
            relationship: Relationship context between parties
            
        Returns:
            List of appropriate relationship terms
        """
        language_lower = language.lower()
        
        # Default to English if language not found
        if language_lower not in self.regional_norms:
            language_lower = "english"
        
        norms = self.regional_norms[language_lower]
        terms = norms["relationship_terms"].get(
            relationship.relationship_type,
            norms["relationship_terms"][RelationshipType.NEW_CUSTOMER]
        )
        
        return terms
    
    def check_festival_pricing(
        self,
        date: datetime,
        region: str,
        commodity: Optional[str] = None
    ) -> Optional[FestivalContext]:
        """
        Checks if current date is near a festival and returns pricing context.
        
        Args:
            date: Date to check
            region: Region/state name
            commodity: Optional commodity name to check specific adjustments
            
        Returns:
            FestivalContext if a festival is active, None otherwise
        """
        month = date.month
        day = date.day
        
        for festival in self.festival_calendar:
            # Check if festival applies to this region
            if region not in festival["regions"] and "Pan-India" not in festival["regions"]:
                continue
            
            # Check if commodity is affected (if specified)
            if commodity:
                affected = festival["affected_commodities"]
                if "all" not in affected and commodity.lower() not in affected:
                    continue
            
            # Check if date falls within festival period
            festival_month = festival["month"]
            day_range = festival["day_range"]
            
            # Skip festivals with no fixed dates (lunar calendar)
            if festival_month is None or day_range is None:
                continue
            
            # Check if within date range (with 7-day buffer before festival)
            if festival_month == month:
                start_day = max(1, day_range[0] - 7)  # 7 days before
                end_day = day_range[1]
                
                if start_day <= day <= end_day:
                    return FestivalContext(
                        festival_name=festival["name"],
                        date=date,
                        typical_price_adjustment=festival["price_adjustment"],
                    )
        
        return None
    
    def get_negotiation_style(self, region: str, language: str) -> NegotiationStyle:
        """
        Returns regional negotiation style preference.
        
        Args:
            region: Region/state name
            language: Language code
            
        Returns:
            NegotiationStyle for the region
        """
        language_lower = language.lower()
        
        # Try to find by language first
        if language_lower in self.regional_norms:
            return self.regional_norms[language_lower]["negotiation_style"]
        
        # Try to find by region
        for lang, norms in self.regional_norms.items():
            if region in norms.get("regions", []):
                return norms["negotiation_style"]
        
        # Default to relationship-focused (most common in India)
        return NegotiationStyle.RELATIONSHIP_FOCUSED
    
    def build_cultural_context(
        self,
        language: str,
        region: str,
        relationship: RelationshipContext,
        date: Optional[datetime] = None,
        commodity: Optional[str] = None
    ) -> CulturalContext:
        """
        Builds complete cultural context for negotiation.
        
        Args:
            language: Language code
            region: Region/state name
            relationship: Relationship context between parties
            date: Optional date for festival checking (defaults to now)
            commodity: Optional commodity for festival-specific adjustments
            
        Returns:
            Complete CulturalContext with all relevant information
        """
        if date is None:
            date = datetime.now()
        
        honorifics = self.get_honorifics(language, relationship)
        relationship_terms = self.get_relationship_terms(language, relationship)
        negotiation_style = self.get_negotiation_style(region, language)
        festival_context = self.check_festival_pricing(date, region, commodity)
        
        return CulturalContext(
            language=language,
            region=region,
            honorifics=honorifics,
            relationship_terms=relationship_terms,
            negotiation_style=negotiation_style,
            festival_context=festival_context,
        )
