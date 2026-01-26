"""Unit tests for PriceCacheManager"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import json

from app.services.price_oracle.price_cache_manager import PriceCacheManager
from app.services.price_oracle.models import (
    Location,
    PriceAggregation,
    PriceSource,
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client"""
    return Mock()


@pytest.fixture
def cache_manager(mock_redis):
    """Create a PriceCacheManager with mock Redis"""
    return PriceCacheManager(mock_redis)


@pytest.fixture
def sample_price_data():
    """Create sample price aggregation data"""
    return PriceAggregation(
        commodity="tomato",
        location=Location(state="Maharashtra", district="Mumbai"),
        min_price=18.0,
        max_price=22.0,
        average_price=20.0,
        median_price=20.0,
        std_dev=1.5,
        sample_size=5,
        sources_used=[PriceSource.DEMO]
    )


def test_generate_cache_key(cache_manager):
    """Test cache key generation"""
    location = Location(state="Maharashtra", district="Mumbai")
    key = cache_manager._generate_cache_key("tomato", location)
    
    assert key == "price:tomato:Maharashtra:Mumbai"


def test_generate_cache_key_without_district(cache_manager):
    """Test cache key generation without district"""
    location = Location(state="Karnataka")
    key = cache_manager._generate_cache_key("onion", location)
    
    assert key == "price:onion:Karnataka:all"


def test_serialize_and_deserialize_price_data(cache_manager, sample_price_data):
    """Test serialization and deserialization of price data"""
    # Serialize
    serialized = cache_manager._serialize_price_data(sample_price_data)
    assert isinstance(serialized, str)
    
    # Deserialize
    deserialized = cache_manager._deserialize_price_data(serialized)
    
    # Verify data integrity
    assert deserialized.commodity == sample_price_data.commodity
    assert deserialized.location.state == sample_price_data.location.state
    assert deserialized.average_price == sample_price_data.average_price
    assert deserialized.min_price == sample_price_data.min_price
    assert deserialized.max_price == sample_price_data.max_price
    assert deserialized.sources_used == sample_price_data.sources_used


def test_cache_price_data_success(cache_manager, mock_redis, sample_price_data):
    """Test successful caching of price data"""
    location = Location(state="Maharashtra")
    
    result = cache_manager.cache_price_data("tomato", location, sample_price_data)
    
    assert result is True
    mock_redis.setex.assert_called_once()
    
    # Verify the call arguments
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == "price:tomato:Maharashtra:all"  # key
    assert call_args[0][1] == 3600  # TTL (1 hour)
    assert isinstance(call_args[0][2], str)  # serialized data


def test_cache_price_data_with_custom_ttl(cache_manager, mock_redis, sample_price_data):
    """Test caching with custom TTL"""
    location = Location(state="Karnataka")
    custom_ttl = 7200  # 2 hours
    
    result = cache_manager.cache_price_data(
        "rice",
        location,
        sample_price_data,
        ttl=custom_ttl
    )
    
    assert result is True
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == custom_ttl


def test_cache_price_data_error_handling(cache_manager, mock_redis, sample_price_data):
    """Test error handling when caching fails"""
    mock_redis.setex.side_effect = Exception("Redis error")
    location = Location(state="Maharashtra")
    
    result = cache_manager.cache_price_data("tomato", location, sample_price_data)
    
    assert result is False


def test_get_cached_price_success(cache_manager, mock_redis, sample_price_data):
    """Test successful retrieval of cached price"""
    location = Location(state="Maharashtra")
    
    # Mock Redis to return serialized data
    serialized = cache_manager._serialize_price_data(sample_price_data)
    mock_redis.get.return_value = serialized
    
    result = cache_manager.get_cached_price("tomato", location)
    
    assert result is not None
    assert result.commodity == "tomato"
    assert result.average_price == 20.0
    mock_redis.get.assert_called_once_with("price:tomato:Maharashtra:all")


def test_get_cached_price_not_found(cache_manager, mock_redis):
    """Test retrieval when no cached data exists"""
    location = Location(state="Maharashtra")
    mock_redis.get.return_value = None
    
    result = cache_manager.get_cached_price("tomato", location)
    
    assert result is None


def test_get_cached_price_error_handling(cache_manager, mock_redis):
    """Test error handling when retrieval fails"""
    location = Location(state="Maharashtra")
    mock_redis.get.side_effect = Exception("Redis error")
    
    result = cache_manager.get_cached_price("tomato", location)
    
    assert result is None


def test_invalidate_cache_success(cache_manager, mock_redis):
    """Test successful cache invalidation"""
    location = Location(state="Maharashtra")
    mock_redis.delete.return_value = 1  # Redis returns number of keys deleted
    
    result = cache_manager.invalidate_cache("tomato", location)
    
    assert result is True
    mock_redis.delete.assert_called_once_with("price:tomato:Maharashtra:all")


def test_invalidate_cache_not_found(cache_manager, mock_redis):
    """Test invalidation when cache doesn't exist"""
    location = Location(state="Maharashtra")
    mock_redis.delete.return_value = 0  # No keys deleted
    
    result = cache_manager.invalidate_cache("tomato", location)
    
    assert result is False


def test_invalidate_cache_error_handling(cache_manager, mock_redis):
    """Test error handling when invalidation fails"""
    location = Location(state="Maharashtra")
    mock_redis.delete.side_effect = Exception("Redis error")
    
    result = cache_manager.invalidate_cache("tomato", location)
    
    assert result is False


def test_cache_for_offline(cache_manager, mock_redis, sample_price_data):
    """Test caching with offline TTL (24 hours)"""
    location = Location(state="Maharashtra")
    
    result = cache_manager.cache_for_offline("tomato", location, sample_price_data)
    
    assert result is True
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == 86400  # 24 hours


def test_get_cache_ttl_success(cache_manager, mock_redis):
    """Test getting remaining TTL"""
    location = Location(state="Maharashtra")
    mock_redis.ttl.return_value = 1800  # 30 minutes remaining
    
    ttl = cache_manager.get_cache_ttl("tomato", location)
    
    assert ttl == 1800
    mock_redis.ttl.assert_called_once_with("price:tomato:Maharashtra:all")


def test_get_cache_ttl_not_found(cache_manager, mock_redis):
    """Test TTL when cache doesn't exist"""
    location = Location(state="Maharashtra")
    mock_redis.ttl.return_value = -2  # Key doesn't exist
    
    ttl = cache_manager.get_cache_ttl("tomato", location)
    
    assert ttl is None


def test_get_cache_ttl_no_expiration(cache_manager, mock_redis):
    """Test TTL when key has no expiration"""
    location = Location(state="Maharashtra")
    mock_redis.ttl.return_value = -1  # No expiration set
    
    ttl = cache_manager.get_cache_ttl("tomato", location)
    
    assert ttl is None


def test_refresh_cache(cache_manager, mock_redis, sample_price_data):
    """Test cache refresh (invalidate + cache)"""
    location = Location(state="Maharashtra")
    mock_redis.delete.return_value = 1
    
    result = cache_manager.refresh_cache("tomato", location, sample_price_data)
    
    assert result is True
    mock_redis.delete.assert_called_once()
    mock_redis.setex.assert_called_once()


def test_is_cache_stale_no_cache(cache_manager, mock_redis):
    """Test staleness check when no cache exists"""
    location = Location(state="Maharashtra")
    mock_redis.get.return_value = None
    
    is_stale = cache_manager.is_cache_stale("tomato", location)
    
    assert is_stale is True


def test_is_cache_stale_fresh_data(cache_manager, mock_redis, sample_price_data):
    """Test staleness check with fresh data"""
    location = Location(state="Maharashtra")
    
    # Create fresh data (current timestamp)
    fresh_data = sample_price_data.model_copy()
    fresh_data.timestamp = datetime.now()
    
    serialized = cache_manager._serialize_price_data(fresh_data)
    mock_redis.get.return_value = serialized
    
    is_stale = cache_manager.is_cache_stale("tomato", location, max_age_seconds=3600)
    
    assert is_stale is False


def test_is_cache_stale_old_data(cache_manager, mock_redis, sample_price_data):
    """Test staleness check with old data"""
    location = Location(state="Maharashtra")
    
    # Create old data (2 hours ago)
    old_data = sample_price_data.model_copy()
    old_data.timestamp = datetime.now() - timedelta(hours=2)
    
    serialized = cache_manager._serialize_price_data(old_data)
    mock_redis.get.return_value = serialized
    
    is_stale = cache_manager.is_cache_stale("tomato", location, max_age_seconds=3600)
    
    assert is_stale is True


def test_cache_key_uniqueness(cache_manager):
    """Test that different commodities/locations generate unique keys"""
    loc1 = Location(state="Maharashtra", district="Mumbai")
    loc2 = Location(state="Maharashtra", district="Pune")
    loc3 = Location(state="Karnataka", district="Mumbai")
    
    key1 = cache_manager._generate_cache_key("tomato", loc1)
    key2 = cache_manager._generate_cache_key("tomato", loc2)
    key3 = cache_manager._generate_cache_key("tomato", loc3)
    key4 = cache_manager._generate_cache_key("onion", loc1)
    
    # All keys should be unique
    keys = [key1, key2, key3, key4]
    assert len(keys) == len(set(keys))
