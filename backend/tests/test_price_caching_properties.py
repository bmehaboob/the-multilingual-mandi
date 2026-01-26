"""Property-based tests for price caching functionality

**Property 33: Data Caching for Offline Access**
**Validates: Requirements 10.4, 12.2**

This module tests the universal properties of the price caching system:
- Requirement 10.4: Cache frequently accessed data including common commodity prices
- Requirement 12.2: Cache last retrieved market average for up to 24 hours
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from unittest.mock import Mock
import time

from app.services.price_oracle.price_cache_manager import PriceCacheManager
from app.services.price_oracle.models import Location, PriceAggregation, PriceSource


# Strategies for generating test data
commodities = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
states = st.sampled_from(["Maharashtra", "Karnataka", "Tamil Nadu", "Andhra Pradesh", "Gujarat", "Punjab"])
districts = st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L',))) | st.none()
prices = st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
ttl_values = st.integers(min_value=1, max_value=86400)  # 1 second to 24 hours


def create_mock_redis():
    """Create a mock Redis client with in-memory storage"""
    storage = {}
    expiry = {}
    
    mock_redis = Mock()
    
    def setex(key, ttl, value):
        storage[key] = value
        expiry[key] = time.time() + ttl
        return True
    
    def get(key):
        if key not in storage:
            return None
        # Check if expired
        if key in expiry and time.time() > expiry[key]:
            del storage[key]
            del expiry[key]
            return None
        return storage[key]
    
    def delete(key):
        if key in storage:
            del storage[key]
            if key in expiry:
                del expiry[key]
            return 1
        return 0
    
    def ttl(key):
        if key not in storage:
            return -2
        if key not in expiry:
            return -1
        remaining = expiry[key] - time.time()
        return int(remaining) if remaining > 0 else -2
    
    mock_redis.setex = setex
    mock_redis.get = get
    mock_redis.delete = delete
    mock_redis.ttl = ttl
    mock_redis._storage = storage
    mock_redis._expiry = expiry
    
    return mock_redis


def create_test_price_data(commodity: str, state: str, average_price: float) -> PriceAggregation:
    """Helper to create price aggregation data for property testing"""
    return PriceAggregation(
        commodity=commodity,
        location=Location(state=state),
        min_price=average_price * 0.8,
        max_price=average_price * 1.2,
        average_price=average_price,
        median_price=average_price,
        std_dev=average_price * 0.1,
        sample_size=10,
        sources_used=[PriceSource.DEMO]
    )


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_cached_data_is_retrievable(commodity: str, state: str, average_price: float):
    """
    Property: Any data that is cached MUST be retrievable before expiration
    
    **Validates: Requirements 10.4, 12.2**
    
    For any commodity, location, and price data that is cached,
    the same data MUST be retrievable via get_cached_price.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    price_data = create_test_price_data(commodity, state, average_price)
    
    # Cache the data
    success = cache_manager.cache_price_data(commodity, location, price_data)
    assert success, "Caching should succeed"
    
    # Retrieve the data
    retrieved_data = cache_manager.get_cached_price(commodity, location)
    
    # Assert: retrieved data must match cached data
    assert retrieved_data is not None, "Cached data should be retrievable"
    assert retrieved_data.commodity == commodity
    assert retrieved_data.location.state == state
    assert retrieved_data.average_price == average_price
    assert retrieved_data.min_price == price_data.min_price
    assert retrieved_data.max_price == price_data.max_price


@given(
    commodity=commodities,
    state=states,
    average_price=prices,
    ttl=ttl_values
)
def test_property_cache_respects_ttl(commodity: str, state: str, average_price: float, ttl: int):
    """
    Property: Cached data MUST respect the specified TTL
    
    **Validates: Requirements 10.4, 12.2**
    
    For any cached data with a specified TTL, the data should be available
    before expiration and unavailable after expiration.
    
    Note: This test uses a mock that simulates TTL behavior.
    """
    assume(ttl >= 1)  # Ensure TTL is at least 1 second
    
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    price_data = create_test_price_data(commodity, state, average_price)
    
    # Cache with custom TTL
    cache_manager.cache_price_data(commodity, location, price_data, ttl=ttl)
    
    # Immediately after caching, data should be available
    retrieved_data = cache_manager.get_cached_price(commodity, location)
    assert retrieved_data is not None, "Data should be available immediately after caching"
    
    # Check TTL is set correctly
    remaining_ttl = cache_manager.get_cache_ttl(commodity, location)
    assert remaining_ttl is not None, "TTL should be set"
    assert remaining_ttl <= ttl, f"Remaining TTL {remaining_ttl} should not exceed set TTL {ttl}"


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_offline_cache_has_extended_ttl(commodity: str, state: str, average_price: float):
    """
    Property: Offline cache MUST have 24-hour TTL
    
    **Validates: Requirements 12.2**
    
    For any data cached for offline access, the TTL must be 24 hours (86400 seconds).
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    price_data = create_test_price_data(commodity, state, average_price)
    
    # Cache for offline
    success = cache_manager.cache_for_offline(commodity, location, price_data)
    assert success, "Offline caching should succeed"
    
    # Check TTL
    remaining_ttl = cache_manager.get_cache_ttl(commodity, location)
    assert remaining_ttl is not None, "TTL should be set for offline cache"
    # Allow small tolerance for execution time
    assert remaining_ttl >= 86390 and remaining_ttl <= 86400, (
        f"Offline cache TTL should be ~86400 seconds (24 hours), got {remaining_ttl}"
    )


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_online_cache_has_standard_ttl(commodity: str, state: str, average_price: float):
    """
    Property: Online cache MUST have 1-hour TTL by default
    
    **Validates: Requirements 10.4**
    
    For any data cached without specifying TTL, the default TTL must be 1 hour (3600 seconds).
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    price_data = create_test_price_data(commodity, state, average_price)
    
    # Cache with default TTL
    success = cache_manager.cache_price_data(commodity, location, price_data)
    assert success, "Caching should succeed"
    
    # Check TTL
    remaining_ttl = cache_manager.get_cache_ttl(commodity, location)
    assert remaining_ttl is not None, "TTL should be set"
    # Allow small tolerance for execution time
    assert remaining_ttl >= 3590 and remaining_ttl <= 3600, (
        f"Default cache TTL should be ~3600 seconds (1 hour), got {remaining_ttl}"
    )


@given(
    commodity=commodities,
    state=states,
    district=districts,
    average_price=prices
)
def test_property_cache_key_uniqueness(commodity: str, state: str, district: str, average_price: float):
    """
    Property: Different commodities or locations MUST have unique cache keys
    
    **Validates: Requirements 10.4**
    
    For any two different commodity-location combinations, the cache keys must be unique
    to prevent data collision.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location1 = Location(state=state, district=district)
    location2 = Location(state=state, district="DifferentDistrict")
    
    price_data1 = create_test_price_data(commodity, state, average_price)
    price_data2 = create_test_price_data(commodity, state, average_price * 1.5)
    
    # Cache data for two different locations
    cache_manager.cache_price_data(commodity, location1, price_data1)
    cache_manager.cache_price_data(commodity, location2, price_data2)
    
    # Retrieve both
    retrieved1 = cache_manager.get_cached_price(commodity, location1)
    retrieved2 = cache_manager.get_cached_price(commodity, location2)
    
    # Assert: both should be retrievable and different
    assert retrieved1 is not None
    assert retrieved2 is not None
    assert retrieved1.average_price == average_price
    assert retrieved2.average_price == average_price * 1.5


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_invalidation_removes_cache(commodity: str, state: str, average_price: float):
    """
    Property: Invalidating cache MUST make data unavailable
    
    **Validates: Requirements 10.4**
    
    For any cached data, calling invalidate_cache must remove the data
    so that subsequent get_cached_price returns None.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    price_data = create_test_price_data(commodity, state, average_price)
    
    # Cache the data
    cache_manager.cache_price_data(commodity, location, price_data)
    
    # Verify it's cached
    assert cache_manager.get_cached_price(commodity, location) is not None
    
    # Invalidate
    success = cache_manager.invalidate_cache(commodity, location)
    assert success, "Invalidation should succeed"
    
    # Verify it's gone
    retrieved = cache_manager.get_cached_price(commodity, location)
    assert retrieved is None, "Data should not be available after invalidation"


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_refresh_updates_cache(commodity: str, state: str, average_price: float):
    """
    Property: Refreshing cache MUST update data with new values
    
    **Validates: Requirements 10.4**
    
    For any cached data, calling refresh_cache with new data must replace
    the old data with the new data.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    old_price_data = create_test_price_data(commodity, state, average_price)
    new_price_data = create_test_price_data(commodity, state, average_price * 2.0)
    
    # Cache old data
    cache_manager.cache_price_data(commodity, location, old_price_data)
    
    # Verify old data is cached
    retrieved = cache_manager.get_cached_price(commodity, location)
    assert retrieved.average_price == average_price
    
    # Refresh with new data
    success = cache_manager.refresh_cache(commodity, location, new_price_data)
    assert success, "Refresh should succeed"
    
    # Verify new data is cached
    retrieved = cache_manager.get_cached_price(commodity, location)
    assert retrieved is not None
    assert retrieved.average_price == average_price * 2.0


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_cache_preserves_data_integrity(commodity: str, state: str, average_price: float):
    """
    Property: Cached data MUST preserve all fields without corruption
    
    **Validates: Requirements 10.4, 12.2**
    
    For any price data cached and retrieved, all fields must match exactly
    (commodity, location, prices, sources, timestamp).
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state, district="TestDistrict")
    price_data = PriceAggregation(
        commodity=commodity,
        location=location,
        min_price=average_price * 0.8,
        max_price=average_price * 1.2,
        average_price=average_price,
        median_price=average_price,
        std_dev=average_price * 0.1,
        sample_size=15,
        sources_used=[PriceSource.DEMO, PriceSource.CROWD_SOURCED]
    )
    
    # Cache the data
    cache_manager.cache_price_data(commodity, location, price_data)
    
    # Retrieve and verify all fields
    retrieved = cache_manager.get_cached_price(commodity, location)
    
    assert retrieved is not None
    assert retrieved.commodity == price_data.commodity
    assert retrieved.location.state == price_data.location.state
    assert retrieved.location.district == price_data.location.district
    assert retrieved.min_price == price_data.min_price
    assert retrieved.max_price == price_data.max_price
    assert retrieved.average_price == price_data.average_price
    assert retrieved.median_price == price_data.median_price
    assert retrieved.std_dev == price_data.std_dev
    assert retrieved.sample_size == price_data.sample_size
    assert retrieved.sources_used == price_data.sources_used
    # Timestamp should be preserved (within small tolerance for serialization)
    assert abs((retrieved.timestamp - price_data.timestamp).total_seconds()) < 1


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_uncached_data_returns_none(commodity: str, state: str, average_price: float):
    """
    Property: Requesting uncached data MUST return None
    
    **Validates: Requirements 10.4**
    
    For any commodity-location combination that has not been cached,
    get_cached_price must return None.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    
    # Try to get data that was never cached
    retrieved = cache_manager.get_cached_price(commodity, location)
    
    assert retrieved is None, "Uncached data should return None"


@given(
    commodity=commodities,
    state=states,
    average_price=prices,
    max_age=st.integers(min_value=1, max_value=86400)
)
def test_property_staleness_check_accuracy(commodity: str, state: str, average_price: float, max_age: int):
    """
    Property: Staleness check MUST accurately determine if cache is stale
    
    **Validates: Requirements 10.4, 12.2**
    
    For any cached data, is_cache_stale should return True if data is older
    than max_age, and False if data is fresh.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    
    # Create fresh data (current timestamp)
    fresh_data = create_test_price_data(commodity, state, average_price)
    fresh_data.timestamp = datetime.now()
    
    # Cache the fresh data
    cache_manager.cache_price_data(commodity, location, fresh_data)
    
    # Check staleness with max_age greater than 0
    is_stale = cache_manager.is_cache_stale(commodity, location, max_age_seconds=max_age)
    
    # Fresh data should not be stale
    assert is_stale is False, f"Fresh data should not be stale with max_age={max_age}"
    
    # Create old data
    old_data = create_test_price_data(commodity, state, average_price)
    old_data.timestamp = datetime.now() - timedelta(seconds=max_age + 100)
    
    # Cache the old data (overwrite)
    cache_manager.cache_price_data(commodity, location, old_data)
    
    # Check staleness
    is_stale = cache_manager.is_cache_stale(commodity, location, max_age_seconds=max_age)
    
    # Old data should be stale
    assert is_stale is True, f"Old data should be stale with max_age={max_age}"


@given(
    commodity=commodities,
    state=states,
    average_price=prices
)
def test_property_cache_operations_are_idempotent(commodity: str, state: str, average_price: float):
    """
    Property: Caching the same data multiple times MUST be idempotent
    
    **Validates: Requirements 10.4**
    
    For any data cached multiple times with the same values, the result
    should be the same as caching once.
    """
    mock_redis = create_mock_redis()
    cache_manager = PriceCacheManager(mock_redis)
    
    location = Location(state=state)
    price_data = create_test_price_data(commodity, state, average_price)
    
    # Cache the same data multiple times
    cache_manager.cache_price_data(commodity, location, price_data)
    cache_manager.cache_price_data(commodity, location, price_data)
    cache_manager.cache_price_data(commodity, location, price_data)
    
    # Retrieve
    retrieved = cache_manager.get_cached_price(commodity, location)
    
    # Should still get the same data
    assert retrieved is not None
    assert retrieved.commodity == commodity
    assert retrieved.average_price == average_price
