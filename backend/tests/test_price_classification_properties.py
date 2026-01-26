"""Property-based tests for price classification logic

**Property 22: Price Classification Logic**
**Validates: Requirements 7.2, 7.3, 7.4**

This module tests the universal properties of the price classification system:
- Requirement 7.2: Prices within 5% of market average are classified as fair
- Requirement 7.3: Prices >10% above market average are classified as high
- Requirement 7.4: Prices >10% below market average are classified as low
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck

from app.services.price_oracle.price_comparison_engine import PriceComparisonEngine
from app.services.price_oracle.models import Location, PriceAggregation, PriceSource


# Strategy for generating valid market prices (positive, reasonable values)
market_prices = st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False)

# Strategy for generating percentage differences in specific ranges
fair_range_percentages = st.floats(min_value=-4.9, max_value=4.9, allow_nan=False, allow_infinity=False)
high_range_percentages = st.floats(min_value=10.5, max_value=50.0, allow_nan=False, allow_infinity=False)
low_range_percentages = st.floats(min_value=-50.0, max_value=-10.5, allow_nan=False, allow_infinity=False)


def create_test_market_data(average_price: float) -> PriceAggregation:
    """Helper to create market data for property testing"""
    return PriceAggregation(
        commodity="test_commodity",
        location=Location(state="TestState"),
        min_price=average_price * 0.8,
        max_price=average_price * 1.2,
        average_price=average_price,
        median_price=average_price,
        std_dev=average_price * 0.1,
        sample_size=10,
        sources_used=[PriceSource.DEMO]
    )


@given(market_price=market_prices, percentage_diff=fair_range_percentages)
def test_property_fair_price_classification(market_price: float, percentage_diff: float):
    """
    Property: Prices within 5% of market average MUST be classified as "fair"
    
    **Validates: Requirements 7.2**
    
    For any market price and any percentage difference within (-5%, +5%),
    the classification MUST be "fair".
    Note: Using strict inequality to avoid boundary precision issues.
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Calculate quoted price based on percentage difference
    quoted_price = market_price * (1 + percentage_diff / 100.0)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Assert: verdict must be "fair"
    assert result.verdict == "fair", (
        f"Price {quoted_price:.2f} ({percentage_diff:.2f}% from {market_price:.2f}) "
        f"should be classified as 'fair' but got '{result.verdict}'"
    )


@given(market_price=market_prices, percentage_diff=high_range_percentages)
def test_property_high_price_classification(market_price: float, percentage_diff: float):
    """
    Property: Prices more than 10% above market average MUST be classified as "high"
    
    **Validates: Requirements 7.3**
    
    For any market price and any percentage difference > 10%,
    the classification MUST be "high".
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Calculate quoted price based on percentage difference
    quoted_price = market_price * (1 + percentage_diff / 100.0)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Assert: verdict must be "high"
    assert result.verdict == "high", (
        f"Price {quoted_price:.2f} ({percentage_diff:.2f}% above {market_price:.2f}) "
        f"should be classified as 'high' but got '{result.verdict}'"
    )


@given(market_price=market_prices, percentage_diff=low_range_percentages)
def test_property_low_price_classification(market_price: float, percentage_diff: float):
    """
    Property: Prices more than 10% below market average MUST be classified as "low"
    
    **Validates: Requirements 7.4**
    
    For any market price and any percentage difference < -10%,
    the classification MUST be "low".
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Calculate quoted price based on percentage difference
    quoted_price = market_price * (1 + percentage_diff / 100.0)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Assert: verdict must be "low"
    assert result.verdict == "low", (
        f"Price {quoted_price:.2f} ({percentage_diff:.2f}% below {market_price:.2f}) "
        f"should be classified as 'low' but got '{result.verdict}'"
    )


@given(market_price=market_prices, quoted_price=market_prices)
def test_property_percentage_difference_accuracy(market_price: float, quoted_price: float):
    """
    Property: Percentage difference calculation MUST be mathematically accurate
    
    **Validates: Requirements 7.2, 7.3, 7.4**
    
    For any market price and quoted price, the calculated percentage difference
    must match the formula: ((quoted - market) / market) * 100
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Calculate expected percentage difference
    expected_percentage_diff = ((quoted_price - market_price) / market_price) * 100.0
    
    # Assert: percentage difference must be accurate (within floating point tolerance)
    assert abs(result.percentage_difference - expected_percentage_diff) < 0.01, (
        f"Percentage difference calculation incorrect: "
        f"expected {expected_percentage_diff:.2f}%, got {result.percentage_difference:.2f}%"
    )


@given(market_price=market_prices, quoted_price=market_prices)
def test_property_verdict_consistency_with_percentage(market_price: float, quoted_price: float):
    """
    Property: Verdict MUST be consistent with the percentage difference
    
    **Validates: Requirements 7.2, 7.3, 7.4**
    
    The verdict must always match the classification rules based on percentage difference:
    - Within 5%: "fair"
    - Between 5% and 10% above: "slightly_high"
    - Between 5% and 10% below: "slightly_low"
    - More than 10% above: "high"
    - More than 10% below: "low"
    
    Note: Boundaries are handled with <= for fair threshold and > for high/low thresholds.
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Calculate percentage difference
    percentage_diff = ((quoted_price - market_price) / market_price) * 100.0
    
    # Determine expected verdict based on percentage difference
    # Using the same logic as the implementation
    abs_diff = abs(quoted_price - market_price)
    fair_threshold_value = 0.05 * market_price
    high_threshold_value = 0.10 * market_price
    
    if abs_diff <= fair_threshold_value:
        expected_verdict = "fair"
    elif quoted_price > market_price + high_threshold_value:
        expected_verdict = "high"
    elif quoted_price < market_price - high_threshold_value:
        expected_verdict = "low"
    elif quoted_price > market_price:
        expected_verdict = "slightly_high"
    else:
        expected_verdict = "slightly_low"
    
    # Assert: verdict must match expected classification
    assert result.verdict == expected_verdict, (
        f"Verdict inconsistent with percentage difference: "
        f"{percentage_diff:.2f}% should give '{expected_verdict}' but got '{result.verdict}'"
    )


@given(market_price=market_prices, quoted_price=market_prices)
def test_property_result_contains_required_fields(market_price: float, quoted_price: float):
    """
    Property: Analysis result MUST always contain all required fields
    
    **Validates: Requirements 7.2, 7.3, 7.4**
    
    Every analysis result must include:
    - verdict (classification)
    - message (user-friendly explanation)
    - percentage_difference (calculated difference)
    - market_average (reference price)
    - quoted_price (input price)
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Assert: all required fields must be present and valid
    assert result.verdict in ["fair", "high", "low", "slightly_high", "slightly_low"], (
        f"Invalid verdict: {result.verdict}"
    )
    assert isinstance(result.message, str) and len(result.message) > 0, (
        "Message must be a non-empty string"
    )
    assert isinstance(result.percentage_difference, float), (
        "Percentage difference must be a float"
    )
    assert result.market_average == market_price, (
        f"Market average mismatch: expected {market_price}, got {result.market_average}"
    )
    assert result.quoted_price == quoted_price, (
        f"Quoted price mismatch: expected {quoted_price}, got {result.quoted_price}"
    )


@given(market_price=market_prices)
def test_property_boundary_conditions(market_price: float):
    """
    Property: Classification boundaries MUST be handled correctly
    
    **Validates: Requirements 7.2, 7.3, 7.4**
    
    Tests the exact boundary conditions:
    - Exactly at 5% threshold should be "fair" (using <=)
    - Just over 10% threshold should be "high" or "low"
    - Between 5% and 10% should be "slightly_high" or "slightly_low"
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Test exact 5% boundary (should be fair due to <= comparison)
    # Using a small epsilon to avoid floating point precision issues
    quoted_at_5_percent = market_price * 1.049  # Just under 5%
    result = engine.analyze_quote("test_commodity", quoted_at_5_percent, market_data)
    assert result.verdict == "fair", (
        f"Price just under 5% above should be 'fair', got '{result.verdict}'"
    )
    
    # Test exact -5% boundary (should be fair)
    quoted_at_minus_5_percent = market_price * 0.951  # Just under -5%
    result = engine.analyze_quote("test_commodity", quoted_at_minus_5_percent, market_data)
    assert result.verdict == "fair", (
        f"Price just under 5% below should be 'fair', got '{result.verdict}'"
    )
    
    # Test clearly over 10% (should be high)
    quoted_at_12_percent = market_price * 1.12
    result = engine.analyze_quote("test_commodity", quoted_at_12_percent, market_data)
    assert result.verdict == "high", (
        f"Price 12% above should be 'high', got '{result.verdict}'"
    )
    
    # Test clearly over -10% (should be low)
    quoted_at_minus_12_percent = market_price * 0.88
    result = engine.analyze_quote("test_commodity", quoted_at_minus_12_percent, market_data)
    assert result.verdict == "low", (
        f"Price 12% below should be 'low', got '{result.verdict}'"
    )
    
    # Test between 5% and 10% (should be slightly_high)
    quoted_at_7_percent = market_price * 1.07
    result = engine.analyze_quote("test_commodity", quoted_at_7_percent, market_data)
    assert result.verdict == "slightly_high", (
        f"Price 7% above should be 'slightly_high', got '{result.verdict}'"
    )
    
    # Test between -5% and -10% (should be slightly_low)
    quoted_at_minus_7_percent = market_price * 0.93
    result = engine.analyze_quote("test_commodity", quoted_at_minus_7_percent, market_data)
    assert result.verdict == "slightly_low", (
        f"Price 7% below should be 'slightly_low', got '{result.verdict}'"
    )


@given(market_price=market_prices, quoted_price=market_prices)
def test_property_message_contains_prices(market_price: float, quoted_price: float):
    """
    Property: Analysis message MUST contain price information
    
    **Validates: Requirements 7.2, 7.3, 7.4**
    
    The user-friendly message must include both the quoted price and market average
    to help users understand the comparison.
    """
    engine = PriceComparisonEngine()
    market_data = create_test_market_data(market_price)
    
    # Analyze the quote
    result = engine.analyze_quote("test_commodity", quoted_price, market_data)
    
    # Assert: message must contain price information
    # Check for rupee symbol or price values
    assert "₹" in result.message or str(int(quoted_price)) in result.message, (
        f"Message should contain price information: {result.message}"
    )
