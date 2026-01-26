"""
Manual test script for Price Oracle functionality
Tests various commodities and scenarios
"""
import asyncio
from app.services.price_oracle.demo_data_provider import DemoDataProvider
from app.services.price_oracle.price_data_aggregator import PriceDataAggregator
from app.services.price_oracle.price_comparison_engine import PriceComparisonEngine
from app.services.price_oracle.models import Location


async def test_price_queries():
    """Test price queries with various commodities"""
    
    print("=" * 60)
    print("MANUAL PRICE ORACLE TEST")
    print("=" * 60)
    print()
    
    # Initialize components
    demo_provider = DemoDataProvider()
    aggregator = PriceDataAggregator()
    comparison_engine = PriceComparisonEngine()
    
    # Test commodities
    test_cases = [
        ("tomato", "Maharashtra", 22.0),
        ("onion", "Karnataka", 30.0),
        ("potato", "Tamil Nadu", 15.0),
        ("rice", "Andhra Pradesh", 35.0),
        ("wheat", "Maharashtra", 25.0),
        ("unknown_commodity", "Maharashtra", 20.0),
    ]
    
    for commodity, state, quoted_price in test_cases:
        print(f"\n{'=' * 60}")
        print(f"Testing: {commodity.upper()} in {state}")
        print(f"Quoted Price: ₹{quoted_price}/kg")
        print(f"{'=' * 60}")
        
        # Get demo prices
        location = Location(state=state, district=f"{state} District")
        prices = await demo_provider.get_demo_prices(commodity, state)
        
        print(f"\nDemo Prices from {len(prices)} mandis:")
        for i, price_data in enumerate(prices, 1):
            print(f"  {i}. {price_data.mandi_name}: ₹{price_data.price}/{price_data.unit}")
        
        # Aggregate prices
        aggregation = await aggregator.aggregate_prices(commodity, location)
        
        print(f"\nPrice Statistics:")
        print(f"  Average: ₹{aggregation.average_price:.2f}")
        print(f"  Minimum: ₹{aggregation.min_price:.2f}")
        print(f"  Maximum: ₹{aggregation.max_price:.2f}")
        print(f"  Median: ₹{aggregation.median_price:.2f}")
        print(f"  Std Dev: ₹{aggregation.std_dev:.2f}")
        
        # Analyze quote
        analysis = comparison_engine.analyze_quote(
            commodity=commodity,
            quoted_price=quoted_price,
            market_data=aggregation
        )
        
        print(f"\nPrice Analysis:")
        print(f"  Verdict: {analysis.verdict.upper()}")
        print(f"  Message: {analysis.message}")
        if analysis.percentage_difference is not None:
            print(f"  Difference: {analysis.percentage_difference:+.1f}%")
        
        # Test price range comparison
        range_message = comparison_engine.get_price_range_message(aggregation)
        print(f"\nPrice Range Info:")
        print(f"  {range_message}")
    
    print(f"\n{'=' * 60}")
    print("TEST COMPLETED SUCCESSFULLY")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(test_price_queries())
