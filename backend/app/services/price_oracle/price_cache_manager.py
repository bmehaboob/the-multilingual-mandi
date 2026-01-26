"""Price cache manager for Redis-based caching"""
import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from redis import Redis

from .models import Location, PriceAggregation


logger = logging.getLogger(__name__)


class PriceCacheManager:
    """
    Manages caching of price data for offline access using Redis.
    
    Cache TTLs:
    - Online cache: 1 hour (3600 seconds)
    - Offline cache: 24 hours (86400 seconds)
    """
    
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.online_cache_ttl = 3600  # 1 hour
        self.offline_cache_ttl = 86400  # 24 hours
    
    def _generate_cache_key(
        self,
        commodity: str,
        location: Location
    ) -> str:
        """
        Generates a unique cache key for commodity and location
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            
        Returns:
            Cache key string
        """
        state = location.state or "unknown"
        district = location.district or "all"
        return f"price:{commodity}:{state}:{district}"
    
    def _serialize_price_data(
        self,
        data: PriceAggregation
    ) -> str:
        """
        Serializes PriceAggregation to JSON string
        
        Args:
            data: Price aggregation data
            
        Returns:
            JSON string
        """
        # Convert to dict and handle datetime serialization
        data_dict = data.model_dump()
        data_dict['timestamp'] = data.timestamp.isoformat()
        data_dict['sources_used'] = [s.value for s in data.sources_used]
        return json.dumps(data_dict)
    
    def _deserialize_price_data(
        self,
        json_str: str
    ) -> PriceAggregation:
        """
        Deserializes JSON string to PriceAggregation
        
        Args:
            json_str: JSON string
            
        Returns:
            PriceAggregation object
        """
        data_dict = json.loads(json_str)
        # Convert timestamp back to datetime
        data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
        return PriceAggregation(**data_dict)
    
    def cache_price_data(
        self,
        commodity: str,
        location: Location,
        data: PriceAggregation,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Caches price data with TTL
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            data: Price aggregation data to cache
            ttl: Time to live in seconds (defaults to online_cache_ttl)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(commodity, location)
            serialized_data = self._serialize_price_data(data)
            
            # Use provided TTL or default to online cache TTL
            cache_ttl = ttl if ttl is not None else self.online_cache_ttl
            
            # Set with expiration
            self.redis_client.setex(
                cache_key,
                cache_ttl,
                serialized_data
            )
            
            logger.info(f"Cached price data for {commodity} in {location.state} with TTL {cache_ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Error caching price data: {e}")
            return False
    
    def get_cached_price(
        self,
        commodity: str,
        location: Location
    ) -> Optional[PriceAggregation]:
        """
        Retrieves cached price if available and fresh
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            
        Returns:
            PriceAggregation if cached and fresh, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(commodity, location)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data is None:
                logger.debug(f"No cached data found for {commodity} in {location.state}")
                return None
            
            # Deserialize and return
            price_data = self._deserialize_price_data(cached_data)
            logger.info(f"Retrieved cached price data for {commodity} in {location.state}")
            return price_data
            
        except Exception as e:
            logger.error(f"Error retrieving cached price data: {e}")
            return None
    
    def invalidate_cache(
        self,
        commodity: str,
        location: Location
    ) -> bool:
        """
        Invalidates (deletes) cached price data
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(commodity, location)
            deleted = self.redis_client.delete(cache_key)
            
            if deleted:
                logger.info(f"Invalidated cache for {commodity} in {location.state}")
                return True
            else:
                logger.debug(f"No cache to invalidate for {commodity} in {location.state}")
                return False
                
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    def cache_for_offline(
        self,
        commodity: str,
        location: Location,
        data: PriceAggregation
    ) -> bool:
        """
        Caches price data with extended TTL for offline access (24 hours)
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            data: Price aggregation data to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        return self.cache_price_data(
            commodity,
            location,
            data,
            ttl=self.offline_cache_ttl
        )
    
    def get_cache_ttl(
        self,
        commodity: str,
        location: Location
    ) -> Optional[int]:
        """
        Gets remaining TTL for cached data
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            
        Returns:
            Remaining TTL in seconds, None if not cached or error
        """
        try:
            cache_key = self._generate_cache_key(commodity, location)
            ttl = self.redis_client.ttl(cache_key)
            
            # Redis returns -2 if key doesn't exist, -1 if no expiration
            if ttl < 0:
                return None
            
            return ttl
            
        except Exception as e:
            logger.error(f"Error getting cache TTL: {e}")
            return None
    
    def refresh_cache(
        self,
        commodity: str,
        location: Location,
        data: PriceAggregation
    ) -> bool:
        """
        Refreshes cached data by invalidating old cache and setting new data
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            data: New price aggregation data
            
        Returns:
            True if refreshed successfully, False otherwise
        """
        self.invalidate_cache(commodity, location)
        return self.cache_price_data(commodity, location, data)
    
    def is_cache_stale(
        self,
        commodity: str,
        location: Location,
        max_age_seconds: int = 3600
    ) -> bool:
        """
        Checks if cached data is stale (older than max_age)
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            max_age_seconds: Maximum age in seconds before considering stale
            
        Returns:
            True if cache is stale or doesn't exist, False if fresh
        """
        cached_data = self.get_cached_price(commodity, location)
        
        if cached_data is None:
            return True
        
        age = datetime.now() - cached_data.timestamp
        return age.total_seconds() > max_age_seconds
