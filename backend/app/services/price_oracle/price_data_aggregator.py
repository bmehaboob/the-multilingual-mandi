"""Price data aggregator with multi-source fallback strategy"""
import logging
from typing import List, Optional
from statistics import mean, median, stdev

from .models import (
    Location,
    PriceAggregation,
    PriceData,
    PriceSource,
)
from .demo_data_provider import DemoDataProvider


logger = logging.getLogger(__name__)


class APIAccessError(Exception):
    """Raised when API access is denied or requires registration"""
    pass


class RegistrationRequiredError(Exception):
    """Raised when API requires registration"""
    pass


class ENAMAPIClient:
    """Client for eNAM API (placeholder for future implementation)"""
    
    async def get_prices(
        self,
        commodity: str,
        state: Optional[str] = None
    ) -> List[PriceData]:
        """
        Fetches prices from eNAM API
        
        Note: eNAM API access may require registration or official partnership.
        This is a placeholder implementation.
        
        Args:
            commodity: Name of the commodity
            state: State name (optional)
            
        Returns:
            List of price data from eNAM
            
        Raises:
            APIAccessError: When API is unavailable
            RegistrationRequiredError: When registration is required
        """
        # Placeholder - will be implemented when eNAM API access is available
        raise RegistrationRequiredError("eNAM API requires registration")


class MandiAPIClient:
    """Client for state mandi board APIs (placeholder for future implementation)"""
    
    async def get_prices(
        self,
        commodity: str,
        state: str
    ) -> List[PriceData]:
        """
        Fetches prices from state mandi board APIs
        
        Args:
            commodity: Name of the commodity
            state: State name
            
        Returns:
            List of price data from mandi boards
            
        Raises:
            APIAccessError: When API is unavailable
        """
        # Placeholder - will be implemented when mandi board APIs are integrated
        raise APIAccessError(f"Mandi board API for {state} is unavailable")


class CrowdSourcePriceDB:
    """Database for crowd-sourced price data (placeholder for future implementation)"""
    
    async def get_prices(
        self,
        commodity: str,
        state: Optional[str] = None,
        radius_km: int = 50
    ) -> List[PriceData]:
        """
        Gets crowd-sourced prices from nearby users
        
        Args:
            commodity: Name of the commodity
            state: State name (optional)
            radius_km: Search radius in kilometers
            
        Returns:
            List of crowd-sourced price data
        """
        # Placeholder - will be implemented when crowd-sourcing is available
        return []


class PriceDataAggregator:
    """
    Aggregates price data from multiple sources with fallback strategy.
    
    Fallback order:
    1. eNAM API (if available)
    2. State Mandi Board APIs
    3. Crowd-sourced data
    4. Demo data (for development and last resort)
    """
    
    def __init__(self):
        self.enam_client = ENAMAPIClient()
        self.mandi_clients = {}  # State-specific mandi board clients
        self.crowd_source_db = CrowdSourcePriceDB()
        self.demo_data_provider = DemoDataProvider()
    
    async def fetch_enam_prices(
        self,
        commodity: str,
        state: Optional[str] = None
    ) -> List[PriceData]:
        """
        Fetches prices from eNAM API with fallback
        
        Note: eNAM API access may require registration or official partnership.
        Falls back to other sources if API is unavailable.
        
        Args:
            commodity: Name of the commodity
            state: State name (optional)
            
        Returns:
            List of prices from eNAM or fallback sources
        """
        try:
            return await self.enam_client.get_prices(commodity, state)
        except (APIAccessError, RegistrationRequiredError) as e:
            logger.warning(f"eNAM API unavailable: {e}. Using fallback data.")
            return await self.get_fallback_prices(commodity, state)
    
    async def get_fallback_prices(
        self,
        commodity: str,
        state: Optional[str] = None
    ) -> List[PriceData]:
        """
        Fallback price data strategy:
        1. Try state mandi board APIs
        2. Try crowd-sourced data
        3. Use demo/synthetic data as last resort
        
        Args:
            commodity: Name of the commodity
            state: State name (optional)
            
        Returns:
            List of price data from available sources
        """
        # Try state mandi boards
        if state and state in self.mandi_clients:
            try:
                prices = await self.mandi_clients[state].get_prices(commodity)
                if prices:
                    logger.info(f"Using mandi board data for {commodity} in {state}")
                    return prices
            except APIAccessError as e:
                logger.warning(f"Mandi board API unavailable: {e}")
        
        # Try crowd-sourced data
        crowd_prices = await self.crowd_source_db.get_prices(commodity, state)
        if crowd_prices:
            logger.info(f"Using crowd-sourced data for {commodity}")
            return crowd_prices
        
        # Last resort: demo data
        logger.info(f"Using demo data for {commodity}")
        return await self.demo_data_provider.get_demo_prices(commodity, state)
    
    async def fetch_mandi_prices(
        self,
        commodity: str,
        state: str
    ) -> List[PriceData]:
        """
        Fetches from state mandi board APIs
        
        Args:
            commodity: Name of the commodity
            state: State name
            
        Returns:
            List of price data from mandi boards
            
        Raises:
            APIAccessError: When API is unavailable
        """
        if state not in self.mandi_clients:
            self.mandi_clients[state] = MandiAPIClient()
        
        return await self.mandi_clients[state].get_prices(commodity, state)
    
    async def get_crowd_sourced_prices(
        self,
        commodity: str,
        location: Location,
        radius_km: int = 50
    ) -> List[PriceData]:
        """
        Gets prices reported by nearby users
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            radius_km: Search radius in kilometers
            
        Returns:
            List of crowd-sourced price data
        """
        return await self.crowd_source_db.get_prices(
            commodity,
            location.state,
            radius_km
        )
    
    async def aggregate_prices(
        self,
        commodity: str,
        location: Location
    ) -> PriceAggregation:
        """
        Combines all sources and calculates statistics
        
        Args:
            commodity: Name of the commodity
            location: Geographic location
            
        Returns:
            Aggregated price statistics with min, max, average, median, std_dev
        """
        # Fetch prices from all available sources
        all_prices: List[PriceData] = []
        sources_used: List[PriceSource] = []
        
        # Try eNAM first
        try:
            enam_prices = await self.fetch_enam_prices(commodity, location.state)
            if enam_prices:
                all_prices.extend(enam_prices)
                # Track actual sources from the price data
                for price in enam_prices:
                    if price.source not in sources_used:
                        sources_used.append(price.source)
        except Exception as e:
            logger.error(f"Error fetching eNAM prices: {e}")
        
        # Try mandi boards
        try:
            mandi_prices = await self.fetch_mandi_prices(commodity, location.state)
            if mandi_prices:
                all_prices.extend(mandi_prices)
                for price in mandi_prices:
                    if price.source not in sources_used:
                        sources_used.append(price.source)
        except Exception as e:
            logger.debug(f"Mandi board prices unavailable: {e}")
        
        # Try crowd-sourced
        try:
            crowd_prices = await self.get_crowd_sourced_prices(commodity, location)
            if crowd_prices:
                all_prices.extend(crowd_prices)
                for price in crowd_prices:
                    if price.source not in sources_used:
                        sources_used.append(price.source)
        except Exception as e:
            logger.debug(f"Crowd-sourced prices unavailable: {e}")
        
        # If no prices found, use demo data
        if not all_prices:
            logger.info(f"No official data available, using demo data for {commodity}")
            demo_prices = await self.demo_data_provider.get_demo_prices(
                commodity,
                location.state
            )
            all_prices.extend(demo_prices)
            for price in demo_prices:
                if price.source not in sources_used:
                    sources_used.append(price.source)
        
        # Calculate statistics
        price_values = [p.price for p in all_prices]
        
        # Handle edge case of single price
        std_deviation = stdev(price_values) if len(price_values) > 1 else 0.0
        
        return PriceAggregation(
            commodity=commodity,
            location=location,
            min_price=min(price_values),
            max_price=max(price_values),
            average_price=mean(price_values),
            median_price=median(price_values),
            std_dev=std_deviation,
            sample_size=len(all_prices),
            sources_used=list(set(sources_used))  # Remove duplicates
        )
