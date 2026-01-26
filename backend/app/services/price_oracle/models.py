"""Data models for Fair Price Oracle"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class PriceSource(str, Enum):
    """Source of price data"""
    ENAM = "enam"
    MANDI_BOARD = "mandi_board"
    CROWD_SOURCED = "crowd_sourced"
    DEMO = "demo"


class Location(BaseModel):
    """Geographic location"""
    state: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PriceData(BaseModel):
    """Individual price data point"""
    id: UUID = Field(default_factory=uuid4)
    commodity: str
    price: float
    unit: str = "kg"
    source: PriceSource
    location: Location
    mandi_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    is_demo: bool = False


class PriceAggregation(BaseModel):
    """Aggregated price statistics"""
    commodity: str
    location: Location
    min_price: float
    max_price: float
    average_price: float
    median_price: float
    std_dev: float
    sample_size: int
    timestamp: datetime = Field(default_factory=datetime.now)
    sources_used: List[PriceSource]


class CommodityPriceData(BaseModel):
    """Demo data structure for commodities"""
    base_price: float
    seasonal_factors: Dict[int, float]  # month -> factor
    regional_variations: Dict[str, float]  # state -> price multiplier
