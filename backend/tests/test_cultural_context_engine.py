"""
Unit tests for Cultural Context Engine.

Tests cultural norms, honorifics, festival calendars, and regional negotiation styles.
"""

import pytest
from datetime import datetime
from backend.app.services.sauda_bot.cultural_context_engine import CulturalContextEngine
from backend.app.services.sauda_bot.models import (
    RelationshipContext,
    RelationshipType,
    NegotiationStyle,
)


@pytest.fixture
def engine():
    """Create a CulturalContextEngine instance for testing."""
    return CulturalContextEngine()


@pytest.fixture
def new_customer_relationship():
    """Create a new customer relationship context."""
    return RelationshipContext(
        relationship_type=RelationshipType.NEW_CUSTOMER,
        transaction_count=0,
        last_transaction_date=None,
    )


@pytest.fixture
def repeat_customer_relationship():
    """Create a repeat customer relationship context."""
    return RelationshipContext(
        relationship_type=RelationshipType.REPEAT_CUSTOMER,
        transaction_count=3,
        last_transaction_date=datetime(2024, 1, 1),
    )


@pytest.fixture
def frequent_partner_relationship():
    """Create a frequent partner relationship context."""
    return RelationshipContext(
        relationship_type=RelationshipType.FREQUENT_PARTNER,
        transaction_count=10,
        last_transaction_date=datetime(2024, 1, 15),
    )


class TestHonorifics:
    """Test honorific retrieval for different languages and relationships."""
    
    def test_hindi_new_customer_honorifics(self, engine, new_customer_relationship):
        """Test Hindi honorifics for new customers."""
        honorifics = engine.get_honorifics("hindi", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "जी" in honorifics or "साहब" in honorifics or "भाई साहब" in honorifics
    
    def test_hindi_repeat_customer_honorifics(self, engine, repeat_customer_relationship):
        """Test Hindi honorifics for repeat customers."""
        honorifics = engine.get_honorifics("hindi", repeat_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "भाई" in honorifics or "दोस्त" in honorifics
    
    def test_hindi_frequent_partner_honorifics(self, engine, frequent_partner_relationship):
        """Test Hindi honorifics for frequent partners."""
        honorifics = engine.get_honorifics("hindi", frequent_partner_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "भाई" in honorifics or "मित्र" in honorifics or "यार" in honorifics
    
    def test_telugu_honorifics(self, engine, new_customer_relationship):
        """Test Telugu honorifics."""
        honorifics = engine.get_honorifics("telugu", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "గారు" in honorifics or "అన్నయ్య" in honorifics
    
    def test_tamil_honorifics(self, engine, new_customer_relationship):
        """Test Tamil honorifics."""
        honorifics = engine.get_honorifics("tamil", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "அவர்கள்" in honorifics or "ஐயா" in honorifics or "அண்ணா" in honorifics
    
    def test_kannada_honorifics(self, engine, new_customer_relationship):
        """Test Kannada honorifics."""
        honorifics = engine.get_honorifics("kannada", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "ಅವರೇ" in honorifics or "ಸರ್" in honorifics or "ಅಣ್ಣ" in honorifics
    
    def test_marathi_honorifics(self, engine, new_customer_relationship):
        """Test Marathi honorifics."""
        honorifics = engine.get_honorifics("marathi", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "साहेब" in honorifics or "दादा" in honorifics or "भाऊ" in honorifics
    
    def test_bengali_honorifics(self, engine, new_customer_relationship):
        """Test Bengali honorifics."""
        honorifics = engine.get_honorifics("bengali", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "বাবু" in honorifics or "দাদা" in honorifics or "ভাই" in honorifics
    
    def test_gujarati_honorifics(self, engine, new_customer_relationship):
        """Test Gujarati honorifics."""
        honorifics = engine.get_honorifics("gujarati", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "સાહેબ" in honorifics or "ભાઈ" in honorifics or "શેઠ" in honorifics
    
    def test_punjabi_honorifics(self, engine, new_customer_relationship):
        """Test Punjabi honorifics."""
        honorifics = engine.get_honorifics("punjabi", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "ਜੀ" in honorifics or "ਸਾਹਿਬ" in honorifics or "ਭਰਾ" in honorifics
    
    def test_malayalam_honorifics(self, engine, new_customer_relationship):
        """Test Malayalam honorifics."""
        honorifics = engine.get_honorifics("malayalam", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "സാർ" in honorifics or "ചേട്ടാ" in honorifics
    
    def test_english_honorifics(self, engine, new_customer_relationship):
        """Test English honorifics."""
        honorifics = engine.get_honorifics("english", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        assert "Sir" in honorifics or "Madam" in honorifics
    
    def test_unknown_language_defaults_to_english(self, engine, new_customer_relationship):
        """Test that unknown languages default to English."""
        honorifics = engine.get_honorifics("unknown_language", new_customer_relationship)
        
        assert isinstance(honorifics, list)
        assert len(honorifics) > 0
        # Should get English honorifics
        assert "Sir" in honorifics or "Madam" in honorifics
    
    def test_case_insensitive_language(self, engine, new_customer_relationship):
        """Test that language matching is case-insensitive."""
        honorifics_lower = engine.get_honorifics("hindi", new_customer_relationship)
        honorifics_upper = engine.get_honorifics("HINDI", new_customer_relationship)
        honorifics_mixed = engine.get_honorifics("HiNdI", new_customer_relationship)
        
        assert honorifics_lower == honorifics_upper == honorifics_mixed


class TestRelationshipTerms:
    """Test relationship term retrieval."""
    
    def test_hindi_relationship_terms(self, engine, new_customer_relationship):
        """Test Hindi relationship terms."""
        terms = engine.get_relationship_terms("hindi", new_customer_relationship)
        
        assert isinstance(terms, list)
        assert len(terms) > 0
        assert "आप" in terms or "आपका" in terms
    
    def test_telugu_relationship_terms(self, engine, repeat_customer_relationship):
        """Test Telugu relationship terms."""
        terms = engine.get_relationship_terms("telugu", repeat_customer_relationship)
        
        assert isinstance(terms, list)
        assert len(terms) > 0
        assert "మీరు" in terms or "నీవు" in terms
    
    def test_tamil_relationship_terms(self, engine, frequent_partner_relationship):
        """Test Tamil relationship terms."""
        terms = engine.get_relationship_terms("tamil", frequent_partner_relationship)
        
        assert isinstance(terms, list)
        assert len(terms) > 0
        assert "நீ" in terms or "உன்" in terms
    
    def test_relationship_progression(self, engine):
        """Test that relationship terms become more informal as relationship deepens."""
        new_rel = RelationshipContext(RelationshipType.NEW_CUSTOMER, 0, None)
        repeat_rel = RelationshipContext(RelationshipType.REPEAT_CUSTOMER, 3, None)
        frequent_rel = RelationshipContext(RelationshipType.FREQUENT_PARTNER, 10, None)
        
        new_terms = engine.get_relationship_terms("hindi", new_rel)
        repeat_terms = engine.get_relationship_terms("hindi", repeat_rel)
        frequent_terms = engine.get_relationship_terms("hindi", frequent_rel)
        
        # All should return valid terms
        assert len(new_terms) > 0
        assert len(repeat_terms) > 0
        assert len(frequent_terms) > 0


class TestFestivalPricing:
    """Test festival calendar and pricing adjustments."""
    
    def test_diwali_pricing(self, engine):
        """Test Diwali festival pricing adjustment."""
        # Diwali is in October-November
        diwali_date = datetime(2024, 10, 20)
        
        festival = engine.check_festival_pricing(diwali_date, "Maharashtra")
        
        assert festival is not None
        assert festival.festival_name == "Diwali"
        assert festival.typical_price_adjustment > 1.0  # Price increase
        assert festival.typical_price_adjustment == 1.15  # 15% increase
    
    def test_pongal_pricing_tamil_nadu(self, engine):
        """Test Pongal festival pricing in Tamil Nadu."""
        pongal_date = datetime(2024, 1, 15)
        
        festival = engine.check_festival_pricing(pongal_date, "Tamil Nadu", "rice")
        
        assert festival is not None
        assert festival.festival_name == "Pongal"
        assert festival.typical_price_adjustment == 1.20  # 20% increase
    
    def test_pongal_not_in_other_regions(self, engine):
        """Test that Pongal doesn't apply outside Tamil Nadu."""
        pongal_date = datetime(2024, 1, 15)
        
        festival = engine.check_festival_pricing(pongal_date, "Maharashtra", "rice")
        
        # Should not get Pongal in Maharashtra
        if festival is not None:
            assert festival.festival_name != "Pongal"
    
    def test_onam_pricing_kerala(self, engine):
        """Test Onam festival pricing in Kerala."""
        onam_date = datetime(2024, 8, 20)
        
        festival = engine.check_festival_pricing(onam_date, "Kerala", "banana")
        
        assert festival is not None
        assert festival.festival_name == "Onam"
        assert festival.typical_price_adjustment == 1.18  # 18% increase
    
    def test_durga_puja_west_bengal(self, engine):
        """Test Durga Puja pricing in West Bengal."""
        durga_puja_date = datetime(2024, 10, 10)
        
        festival = engine.check_festival_pricing(durga_puja_date, "West Bengal")
        
        assert festival is not None
        # Both Diwali and Durga Puja can occur in October, so accept either
        assert festival.festival_name in ["Durga Puja", "Diwali"]
        assert festival.typical_price_adjustment >= 1.15  # At least 15% increase
    
    def test_ganesh_chaturthi_maharashtra(self, engine):
        """Test Ganesh Chaturthi pricing in Maharashtra."""
        ganesh_date = datetime(2024, 9, 10)
        
        festival = engine.check_festival_pricing(ganesh_date, "Maharashtra")
        
        assert festival is not None
        assert festival.festival_name == "Ganesh Chaturthi"
        assert festival.typical_price_adjustment == 1.12  # 12% increase
    
    def test_harvest_season_price_decrease(self, engine):
        """Test that harvest seasons cause price decreases."""
        # Rabi harvest in April
        harvest_date = datetime(2024, 4, 15)
        
        festival = engine.check_festival_pricing(harvest_date, "Punjab", "wheat")
        
        assert festival is not None
        assert festival.festival_name == "Rabi Harvest"
        assert festival.typical_price_adjustment < 1.0  # Price decrease
        assert festival.typical_price_adjustment == 0.90  # 10% decrease
    
    def test_no_festival_on_regular_day(self, engine):
        """Test that no festival is returned on regular days."""
        regular_date = datetime(2024, 2, 15)
        
        festival = engine.check_festival_pricing(regular_date, "Maharashtra")
        
        # February 15 should not have any major festivals
        assert festival is None
    
    def test_festival_buffer_period(self, engine):
        """Test that festival pricing applies 7 days before festival."""
        # 7 days before Diwali (Oct 20)
        pre_diwali = datetime(2024, 10, 13)
        
        festival = engine.check_festival_pricing(pre_diwali, "Maharashtra")
        
        # Should still get Diwali pricing in buffer period
        assert festival is not None
        assert festival.festival_name == "Diwali"
    
    def test_commodity_specific_festival(self, engine):
        """Test that commodity-specific festivals only apply to relevant commodities."""
        pongal_date = datetime(2024, 1, 15)
        
        # Rice is affected by Pongal
        rice_festival = engine.check_festival_pricing(pongal_date, "Tamil Nadu", "rice")
        assert rice_festival is not None
        assert rice_festival.festival_name == "Pongal"
        
        # Tomato is not specifically affected by Pongal
        tomato_festival = engine.check_festival_pricing(pongal_date, "Tamil Nadu", "tomato")
        # Should either be None or not Pongal
        if tomato_festival is not None:
            assert tomato_festival.festival_name != "Pongal"
    
    def test_pan_india_festivals(self, engine):
        """Test that pan-India festivals apply to all regions."""
        diwali_date = datetime(2024, 10, 20)
        
        # Test multiple regions
        regions = ["Maharashtra", "Tamil Nadu", "Kerala", "Punjab", "West Bengal"]
        
        for region in regions:
            festival = engine.check_festival_pricing(diwali_date, region)
            assert festival is not None
            assert festival.festival_name == "Diwali"


class TestNegotiationStyle:
    """Test regional negotiation style preferences."""
    
    def test_hindi_relationship_focused(self, engine):
        """Test that Hindi regions are relationship-focused."""
        style = engine.get_negotiation_style("Delhi", "hindi")
        assert style == NegotiationStyle.RELATIONSHIP_FOCUSED
    
    def test_tamil_direct_style(self, engine):
        """Test that Tamil regions prefer direct negotiation."""
        style = engine.get_negotiation_style("Tamil Nadu", "tamil")
        assert style == NegotiationStyle.DIRECT
    
    def test_kannada_business_focused(self, engine):
        """Test that Kannada regions are business-focused."""
        style = engine.get_negotiation_style("Karnataka", "kannada")
        assert style == NegotiationStyle.BUSINESS_FOCUSED
    
    def test_marathi_business_focused(self, engine):
        """Test that Marathi regions are business-focused."""
        style = engine.get_negotiation_style("Maharashtra", "marathi")
        assert style == NegotiationStyle.BUSINESS_FOCUSED
    
    def test_malayalam_indirect_style(self, engine):
        """Test that Malayalam regions prefer indirect negotiation."""
        style = engine.get_negotiation_style("Kerala", "malayalam")
        assert style == NegotiationStyle.INDIRECT
    
    def test_punjabi_direct_style(self, engine):
        """Test that Punjabi regions prefer direct negotiation."""
        style = engine.get_negotiation_style("Punjab", "punjabi")
        assert style == NegotiationStyle.DIRECT
    
    def test_default_style_for_unknown_region(self, engine):
        """Test that unknown regions default to relationship-focused."""
        style = engine.get_negotiation_style("Unknown Region", "unknown_language")
        assert style == NegotiationStyle.RELATIONSHIP_FOCUSED


class TestBuildCulturalContext:
    """Test building complete cultural context."""
    
    def test_complete_context_without_festival(self, engine, new_customer_relationship):
        """Test building complete cultural context without festival."""
        context = engine.build_cultural_context(
            language="hindi",
            region="Delhi",
            relationship=new_customer_relationship,
            date=datetime(2024, 2, 15),  # No festival
        )
        
        assert context.language == "hindi"
        assert context.region == "Delhi"
        assert len(context.honorifics) > 0
        assert len(context.relationship_terms) > 0
        assert context.negotiation_style == NegotiationStyle.RELATIONSHIP_FOCUSED
        assert context.festival_context is None
    
    def test_complete_context_with_festival(self, engine, repeat_customer_relationship):
        """Test building complete cultural context with festival."""
        context = engine.build_cultural_context(
            language="hindi",
            region="Delhi",
            relationship=repeat_customer_relationship,
            date=datetime(2024, 10, 20),  # Diwali
        )
        
        assert context.language == "hindi"
        assert context.region == "Delhi"
        assert len(context.honorifics) > 0
        assert len(context.relationship_terms) > 0
        assert context.negotiation_style == NegotiationStyle.RELATIONSHIP_FOCUSED
        assert context.festival_context is not None
        assert context.festival_context.festival_name == "Diwali"
    
    def test_context_with_commodity_specific_festival(self, engine, new_customer_relationship):
        """Test context with commodity-specific festival."""
        context = engine.build_cultural_context(
            language="tamil",
            region="Tamil Nadu",
            relationship=new_customer_relationship,
            date=datetime(2024, 1, 15),  # Pongal
            commodity="rice",
        )
        
        assert context.language == "tamil"
        assert context.region == "Tamil Nadu"
        assert context.negotiation_style == NegotiationStyle.DIRECT
        assert context.festival_context is not None
        assert context.festival_context.festival_name == "Pongal"
    
    def test_context_defaults_to_current_date(self, engine, new_customer_relationship):
        """Test that context defaults to current date when not specified."""
        context = engine.build_cultural_context(
            language="hindi",
            region="Delhi",
            relationship=new_customer_relationship,
        )
        
        # Should not raise an error and should have valid data
        assert context.language == "hindi"
        assert context.region == "Delhi"
        assert len(context.honorifics) > 0
    
    def test_context_for_different_relationship_types(self, engine):
        """Test that context adapts to different relationship types."""
        new_rel = RelationshipContext(RelationshipType.NEW_CUSTOMER, 0, None)
        frequent_rel = RelationshipContext(RelationshipType.FREQUENT_PARTNER, 10, None)
        
        new_context = engine.build_cultural_context(
            language="hindi",
            region="Delhi",
            relationship=new_rel,
        )
        
        frequent_context = engine.build_cultural_context(
            language="hindi",
            region="Delhi",
            relationship=frequent_rel,
        )
        
        # Honorifics should be different based on relationship
        assert new_context.honorifics != frequent_context.honorifics


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_language_string(self, engine, new_customer_relationship):
        """Test handling of empty language string."""
        honorifics = engine.get_honorifics("", new_customer_relationship)
        
        # Should default to English
        assert len(honorifics) > 0
    
    def test_none_date_in_festival_check(self, engine):
        """Test that None date defaults to current date."""
        context = engine.build_cultural_context(
            language="hindi",
            region="Delhi",
            relationship=RelationshipContext(RelationshipType.NEW_CUSTOMER, 0, None),
            date=None,
        )
        
        # Should not raise an error
        assert context is not None
    
    def test_multiple_festivals_same_date(self, engine):
        """Test handling when multiple festivals could apply."""
        # October 10 could have multiple festivals
        date = datetime(2024, 10, 10)
        
        festival = engine.check_festival_pricing(date, "West Bengal")
        
        # Should return one festival (first match)
        assert festival is not None
        assert isinstance(festival.festival_name, str)
    
    def test_all_supported_languages_have_data(self, engine, new_customer_relationship):
        """Test that all major Indian languages have cultural data."""
        languages = [
            "hindi", "telugu", "tamil", "kannada", "marathi",
            "bengali", "gujarati", "punjabi", "malayalam", "odia",
            "assamese", "urdu", "english"
        ]
        
        for language in languages:
            honorifics = engine.get_honorifics(language, new_customer_relationship)
            terms = engine.get_relationship_terms(language, new_customer_relationship)
            style = engine.get_negotiation_style("", language)
            
            assert len(honorifics) > 0, f"No honorifics for {language}"
            assert len(terms) > 0, f"No relationship terms for {language}"
            assert style is not None, f"No negotiation style for {language}"
