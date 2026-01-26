"""
Manual test script for Cultural Context Engine.

This script demonstrates the functionality of the CulturalContextEngine
with various scenarios.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from app.services.sauda_bot.cultural_context_engine import CulturalContextEngine
from app.services.sauda_bot.models import RelationshipContext, RelationshipType


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_honorifics():
    """Test honorifics for different languages and relationships."""
    print_section("Testing Honorifics")
    
    engine = CulturalContextEngine()
    
    # Test different relationship types
    relationships = [
        (RelationshipType.NEW_CUSTOMER, "New Customer"),
        (RelationshipType.REPEAT_CUSTOMER, "Repeat Customer"),
        (RelationshipType.FREQUENT_PARTNER, "Frequent Partner"),
    ]
    
    languages = ["hindi", "telugu", "tamil", "kannada", "marathi"]
    
    for lang in languages:
        print(f"\n{lang.upper()}:")
        for rel_type, rel_name in relationships:
            rel = RelationshipContext(rel_type, 0, None)
            honorifics = engine.get_honorifics(lang, rel)
            print(f"  {rel_name}: {', '.join(honorifics)}")


def test_festival_pricing():
    """Test festival pricing adjustments."""
    print_section("Testing Festival Pricing")
    
    engine = CulturalContextEngine()
    
    # Test various dates and regions
    test_cases = [
        (datetime(2024, 10, 20), "Maharashtra", "tomato", "Diwali in Maharashtra"),
        (datetime(2024, 1, 15), "Tamil Nadu", "rice", "Pongal in Tamil Nadu"),
        (datetime(2024, 8, 20), "Kerala", "banana", "Onam in Kerala"),
        (datetime(2024, 10, 10), "West Bengal", None, "Durga Puja in West Bengal"),
        (datetime(2024, 4, 15), "Punjab", "wheat", "Rabi Harvest in Punjab"),
        (datetime(2024, 2, 15), "Delhi", None, "Regular day (no festival)"),
    ]
    
    for date, region, commodity, description in test_cases:
        festival = engine.check_festival_pricing(date, region, commodity)
        print(f"\n{description}:")
        if festival:
            print(f"  Festival: {festival.festival_name}")
            print(f"  Price Adjustment: {festival.typical_price_adjustment:.2f}x")
            adjustment_pct = (festival.typical_price_adjustment - 1) * 100
            if adjustment_pct > 0:
                print(f"  Impact: +{adjustment_pct:.0f}% price increase")
            else:
                print(f"  Impact: {adjustment_pct:.0f}% price decrease")
        else:
            print("  No festival - normal pricing")


def test_negotiation_styles():
    """Test regional negotiation styles."""
    print_section("Testing Negotiation Styles")
    
    engine = CulturalContextEngine()
    
    test_cases = [
        ("Delhi", "hindi", "Hindi-speaking North India"),
        ("Tamil Nadu", "tamil", "Tamil Nadu"),
        ("Karnataka", "kannada", "Karnataka"),
        ("Maharashtra", "marathi", "Maharashtra"),
        ("Kerala", "malayalam", "Kerala"),
        ("Punjab", "punjabi", "Punjab"),
    ]
    
    for region, language, description in test_cases:
        style = engine.get_negotiation_style(region, language)
        print(f"\n{description}:")
        print(f"  Negotiation Style: {style.value}")


def test_complete_cultural_context():
    """Test building complete cultural context."""
    print_section("Testing Complete Cultural Context")
    
    engine = CulturalContextEngine()
    
    # Scenario 1: New customer during Diwali
    print("\nScenario 1: New Hindi-speaking customer in Delhi during Diwali")
    rel1 = RelationshipContext(RelationshipType.NEW_CUSTOMER, 0, None)
    context1 = engine.build_cultural_context(
        language="hindi",
        region="Delhi",
        relationship=rel1,
        date=datetime(2024, 10, 20),
        commodity="tomato"
    )
    
    print(f"  Language: {context1.language}")
    print(f"  Region: {context1.region}")
    print(f"  Honorifics: {', '.join(context1.honorifics)}")
    print(f"  Relationship Terms: {', '.join(context1.relationship_terms)}")
    print(f"  Negotiation Style: {context1.negotiation_style.value}")
    if context1.festival_context:
        print(f"  Festival: {context1.festival_context.festival_name}")
        print(f"  Price Adjustment: {context1.festival_context.typical_price_adjustment:.2f}x")
    
    # Scenario 2: Frequent partner in Tamil Nadu during Pongal
    print("\nScenario 2: Frequent Tamil-speaking partner in Tamil Nadu during Pongal")
    rel2 = RelationshipContext(RelationshipType.FREQUENT_PARTNER, 15, datetime(2024, 1, 1))
    context2 = engine.build_cultural_context(
        language="tamil",
        region="Tamil Nadu",
        relationship=rel2,
        date=datetime(2024, 1, 15),
        commodity="rice"
    )
    
    print(f"  Language: {context2.language}")
    print(f"  Region: {context2.region}")
    print(f"  Honorifics: {', '.join(context2.honorifics)}")
    print(f"  Relationship Terms: {', '.join(context2.relationship_terms)}")
    print(f"  Negotiation Style: {context2.negotiation_style.value}")
    if context2.festival_context:
        print(f"  Festival: {context2.festival_context.festival_name}")
        print(f"  Price Adjustment: {context2.festival_context.typical_price_adjustment:.2f}x")
    
    # Scenario 3: Repeat customer in Kerala (no festival)
    print("\nScenario 3: Repeat Malayalam-speaking customer in Kerala (regular day)")
    rel3 = RelationshipContext(RelationshipType.REPEAT_CUSTOMER, 3, datetime(2024, 1, 1))
    context3 = engine.build_cultural_context(
        language="malayalam",
        region="Kerala",
        relationship=rel3,
        date=datetime(2024, 2, 15),
    )
    
    print(f"  Language: {context3.language}")
    print(f"  Region: {context3.region}")
    print(f"  Honorifics: {', '.join(context3.honorifics)}")
    print(f"  Relationship Terms: {', '.join(context3.relationship_terms)}")
    print(f"  Negotiation Style: {context3.negotiation_style.value}")
    if context3.festival_context:
        print(f"  Festival: {context3.festival_context.festival_name}")
    else:
        print(f"  Festival: None (regular day)")


def test_price_adjustment_examples():
    """Test practical price adjustment examples."""
    print_section("Practical Price Adjustment Examples")
    
    engine = CulturalContextEngine()
    
    base_price = 50.0  # Rs per kg
    
    scenarios = [
        (datetime(2024, 10, 20), "Maharashtra", "tomato", "Diwali"),
        (datetime(2024, 1, 15), "Tamil Nadu", "rice", "Pongal"),
        (datetime(2024, 4, 15), "Punjab", "wheat", "Rabi Harvest"),
    ]
    
    for date, region, commodity, description in scenarios:
        festival = engine.check_festival_pricing(date, region, commodity)
        
        print(f"\n{description}:")
        print(f"  Base Price: ₹{base_price:.2f} per kg")
        
        if festival:
            adjusted_price = base_price * festival.typical_price_adjustment
            print(f"  Festival: {festival.festival_name}")
            print(f"  Adjustment Factor: {festival.typical_price_adjustment:.2f}x")
            print(f"  Adjusted Price: ₹{adjusted_price:.2f} per kg")
            
            difference = adjusted_price - base_price
            if difference > 0:
                print(f"  Impact: +₹{difference:.2f} ({(difference/base_price)*100:.0f}% increase)")
            else:
                print(f"  Impact: ₹{difference:.2f} ({(difference/base_price)*100:.0f}% decrease)")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 70)
    print("  CULTURAL CONTEXT ENGINE - MANUAL TEST")
    print("=" * 70)
    
    try:
        test_honorifics()
        test_festival_pricing()
        test_negotiation_styles()
        test_complete_cultural_context()
        test_price_adjustment_examples()
        
        print("\n" + "=" * 70)
        print("  ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
