"""
Example usage of Data Anonymization Service

This example demonstrates how to anonymize user data before sharing with
third parties for price aggregation and market intelligence.

Requirements: 15.3 - Data anonymization for third-party sharing
"""
from datetime import datetime
from uuid import uuid4
from app.services.privacy.data_anonymizer import DataAnonymizer


def example_anonymize_transaction():
    """
    Example: Anonymize a completed transaction before sharing with
    third-party market intelligence services.
    """
    print("=" * 60)
    print("Example 1: Anonymizing a Transaction")
    print("=" * 60)
    
    # Initialize the anonymizer
    anonymizer = DataAnonymizer()
    
    # Sample transaction with PII
    transaction = {
        "buyer_id": uuid4(),
        "seller_id": uuid4(),
        "commodity": "tomato",
        "agreed_price": 25.50,
        "quantity": 100.0,
        "unit": "kg",
        "market_average_at_time": 24.00,
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "latitude": 18.5204,  # PII - exact location
            "longitude": 73.8567,  # PII - exact location
            "address": "123 Market Street"  # PII - address
        },
        "completed_at": datetime(2024, 1, 15, 10, 30, 0)
    }
    
    print("\nOriginal transaction (contains PII):")
    print(f"  Buyer ID: {transaction['buyer_id']}")
    print(f"  Seller ID: {transaction['seller_id']}")
    print(f"  Location: {transaction['location']}")
    
    # Anonymize the transaction
    anonymized = anonymizer.anonymize_transaction(transaction)
    
    print("\nAnonymized transaction (PII removed):")
    print(f"  Commodity: {anonymized.commodity}")
    print(f"  Price: {anonymized.agreed_price} per {anonymized.unit}")
    print(f"  Quantity: {anonymized.quantity} {anonymized.unit}")
    print(f"  State: {anonymized.state}")
    print(f"  District: {anonymized.district}")
    print(f"  Anonymized Buyer: {anonymized.anonymized_buyer_id[:16]}...")
    print(f"  Anonymized Seller: {anonymized.anonymized_seller_id[:16]}...")
    print(f"  Completed: {anonymized.completed_at}")
    
    # Verify no PII remains
    data_dict = anonymized.model_dump()
    is_clean = anonymizer.verify_no_pii(data_dict)
    print(f"\n✓ PII verification: {'PASSED' if is_clean else 'FAILED'}")
    
    return anonymized


def example_anonymize_price_contribution():
    """
    Example: Anonymize a user's price contribution for crowd-sourced
    price aggregation.
    """
    print("\n" + "=" * 60)
    print("Example 2: Anonymizing a Price Contribution")
    print("=" * 60)
    
    # Initialize the anonymizer
    anonymizer = DataAnonymizer()
    
    # User contributing price data
    user_id = uuid4()
    
    print(f"\nOriginal user ID (PII): {user_id}")
    
    # Anonymize the price contribution
    anonymized = anonymizer.anonymize_price_contribution(
        user_id=user_id,
        commodity="onion",
        price=30.00,
        quantity=50.0,
        unit="kg",
        location={
            "state": "Karnataka",
            "district": "Bangalore",
            "latitude": 12.9716,  # PII - will be removed
            "longitude": 77.5946,  # PII - will be removed
            "street": "MG Road"  # PII - will be removed
        },
        timestamp=datetime(2024, 1, 15, 14, 0, 0)
    )
    
    print("\nAnonymized price contribution:")
    print(f"  Commodity: {anonymized.commodity}")
    print(f"  Price: {anonymized.price} per {anonymized.unit}")
    print(f"  Quantity: {anonymized.quantity} {anonymized.unit}")
    print(f"  State: {anonymized.state}")
    print(f"  District: {anonymized.district}")
    print(f"  Anonymized User: {anonymized.anonymized_user_id[:16]}...")
    print(f"  Timestamp: {anonymized.timestamp}")
    
    # Verify no PII remains
    data_dict = anonymized.model_dump()
    is_clean = anonymizer.verify_no_pii(data_dict)
    print(f"\n✓ PII verification: {'PASSED' if is_clean else 'FAILED'}")
    
    return anonymized


def example_bulk_anonymization():
    """
    Example: Anonymize multiple transactions in bulk for efficient
    processing when sharing data with third parties.
    """
    print("\n" + "=" * 60)
    print("Example 3: Bulk Anonymization")
    print("=" * 60)
    
    # Initialize the anonymizer
    anonymizer = DataAnonymizer()
    
    # Multiple transactions to anonymize
    transactions = [
        {
            "buyer_id": uuid4(),
            "seller_id": uuid4(),
            "commodity": "tomato",
            "agreed_price": 25.00,
            "quantity": 100.0,
            "unit": "kg",
            "market_average_at_time": 24.00,
            "location": {"state": "Maharashtra", "district": "Pune"},
            "completed_at": datetime(2024, 1, 15, 10, 0, 0)
        },
        {
            "buyer_id": uuid4(),
            "seller_id": uuid4(),
            "commodity": "onion",
            "agreed_price": 30.00,
            "quantity": 75.0,
            "unit": "kg",
            "market_average_at_time": 28.00,
            "location": {"state": "Karnataka", "district": "Bangalore"},
            "completed_at": datetime(2024, 1, 15, 11, 0, 0)
        },
        {
            "buyer_id": uuid4(),
            "seller_id": uuid4(),
            "commodity": "potato",
            "agreed_price": 18.00,
            "quantity": 150.0,
            "unit": "kg",
            "market_average_at_time": 17.50,
            "location": {"state": "Tamil Nadu", "district": "Chennai"},
            "completed_at": datetime(2024, 1, 15, 12, 0, 0)
        }
    ]
    
    print(f"\nAnonymizing {len(transactions)} transactions...")
    
    # Bulk anonymization
    anonymized_list = anonymizer.anonymize_bulk_transactions(transactions)
    
    print(f"\nAnonymized {len(anonymized_list)} transactions:")
    for i, anonymized in enumerate(anonymized_list, 1):
        print(f"\n  Transaction {i}:")
        print(f"    Commodity: {anonymized.commodity}")
        print(f"    Price: {anonymized.agreed_price} per {anonymized.unit}")
        print(f"    Location: {anonymized.state}, {anonymized.district}")
    
    print(f"\n✓ All transactions anonymized successfully")
    
    return anonymized_list


def example_consistent_anonymization():
    """
    Example: Demonstrate that the same user always gets the same
    anonymized ID, allowing pattern detection without identification.
    """
    print("\n" + "=" * 60)
    print("Example 4: Consistent Anonymization")
    print("=" * 60)
    
    # Initialize the anonymizer
    anonymizer = DataAnonymizer()
    
    # Same user making multiple contributions
    user_id = uuid4()
    
    print(f"\nUser ID: {user_id}")
    print("\nUser makes 3 price contributions:")
    
    # First contribution
    contrib1 = anonymizer.anonymize_price_contribution(
        user_id=user_id,
        commodity="tomato",
        price=25.00,
        quantity=100.0,
        unit="kg"
    )
    print(f"\n  Contribution 1 (tomato):")
    print(f"    Anonymized ID: {contrib1.anonymized_user_id[:16]}...")
    
    # Second contribution
    contrib2 = anonymizer.anonymize_price_contribution(
        user_id=user_id,
        commodity="onion",
        price=30.00,
        quantity=50.0,
        unit="kg"
    )
    print(f"\n  Contribution 2 (onion):")
    print(f"    Anonymized ID: {contrib2.anonymized_user_id[:16]}...")
    
    # Third contribution
    contrib3 = anonymizer.anonymize_price_contribution(
        user_id=user_id,
        commodity="potato",
        price=18.00,
        quantity=75.0,
        unit="kg"
    )
    print(f"\n  Contribution 3 (potato):")
    print(f"    Anonymized ID: {contrib3.anonymized_user_id[:16]}...")
    
    # Verify consistency
    all_same = (
        contrib1.anonymized_user_id == contrib2.anonymized_user_id == 
        contrib3.anonymized_user_id
    )
    
    print(f"\n✓ Consistency check: {'PASSED' if all_same else 'FAILED'}")
    print("  (Same user always gets same anonymized ID)")
    
    return contrib1, contrib2, contrib3


def example_integration_with_price_aggregation():
    """
    Example: Show how anonymization integrates with price aggregation
    for third-party sharing.
    """
    print("\n" + "=" * 60)
    print("Example 5: Integration with Price Aggregation")
    print("=" * 60)
    
    # Initialize the anonymizer
    anonymizer = DataAnonymizer()
    
    print("\nScenario: Multiple users contribute price data for 'tomato'")
    print("          Data will be shared with third-party analytics service")
    
    # Simulate multiple users contributing price data
    contributions = []
    for i in range(5):
        user_id = uuid4()
        price = 24.0 + (i * 0.5)  # Varying prices
        
        anonymized = anonymizer.anonymize_price_contribution(
            user_id=user_id,
            commodity="tomato",
            price=price,
            quantity=100.0,
            unit="kg",
            location={"state": "Maharashtra", "district": "Pune"}
        )
        contributions.append(anonymized)
    
    print(f"\nCollected {len(contributions)} anonymized price contributions:")
    for i, contrib in enumerate(contributions, 1):
        print(f"  {i}. Price: ₹{contrib.price}/kg from {contrib.state}")
    
    # Calculate aggregate statistics (safe to share with third parties)
    prices = [c.price for c in contributions]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    print(f"\nAggregate statistics (safe to share):")
    print(f"  Average: ₹{avg_price:.2f}/kg")
    print(f"  Range: ₹{min_price:.2f} - ₹{max_price:.2f}/kg")
    print(f"  Sample size: {len(contributions)}")
    print(f"  Location: Maharashtra, Pune")
    
    print(f"\n✓ Data ready for third-party sharing (no PII)")
    
    return contributions


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("DATA ANONYMIZATION SERVICE - USAGE EXAMPLES")
    print("=" * 60)
    print("\nThese examples demonstrate how to anonymize user data before")
    print("sharing with third parties for price aggregation and market")
    print("intelligence, in compliance with Requirement 15.3.")
    
    # Run all examples
    example_anonymize_transaction()
    example_anonymize_price_contribution()
    example_bulk_anonymization()
    example_consistent_anonymization()
    example_integration_with_price_aggregation()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. All PII (names, IDs, exact locations) is removed")
    print("  2. Only coarse location (state/district) is preserved")
    print("  3. User IDs are replaced with one-way hashes")
    print("  4. Same user always gets same anonymized ID (for patterns)")
    print("  5. Market intelligence data is preserved")
    print("  6. Data is safe to share with third parties")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
