"""Transaction schemas for API requests and responses"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


class CreateTransactionRequest(BaseModel):
    """Request to create a new transaction"""
    buyer_id: str = Field(..., description="Buyer user ID")
    seller_id: str = Field(..., description="Seller user ID")
    commodity: str = Field(..., description="Commodity name", min_length=1, max_length=255)
    quantity: float = Field(..., description="Quantity traded", gt=0)
    unit: str = Field(..., description="Unit of measurement", min_length=1, max_length=50)
    agreed_price: float = Field(..., description="Final agreed price per unit", ge=0)
    market_average_at_time: Optional[float] = Field(
        None,
        description="Market average price at transaction time",
        ge=0
    )
    conversation_id: Optional[str] = Field(None, description="Associated conversation ID")
    location: Optional[Dict] = Field(None, description="Location data (state, district, etc.)")
    
    @validator('buyer_id', 'seller_id', 'conversation_id')
    def validate_uuid(cls, v, field):
        """Validate UUID format"""
        if v is not None:
            try:
                UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format for {field.name}: {v}")
        return v
    
    @validator('seller_id')
    def validate_different_parties(cls, v, values):
        """Ensure buyer and seller are different"""
        if 'buyer_id' in values and v == values['buyer_id']:
            raise ValueError("Buyer and seller must be different users")
        return v


class TransactionResponse(BaseModel):
    """Response containing transaction details"""
    id: str = Field(..., description="Transaction ID")
    buyer_id: str = Field(..., description="Buyer user ID")
    seller_id: str = Field(..., description="Seller user ID")
    commodity: str = Field(..., description="Commodity name")
    quantity: float = Field(..., description="Quantity traded")
    unit: str = Field(..., description="Unit of measurement")
    agreed_price: float = Field(..., description="Agreed price per unit")
    market_average_at_time: Optional[float] = Field(None, description="Market average at time")
    conversation_id: Optional[str] = Field(None, description="Associated conversation ID")
    completed_at: datetime = Field(..., description="Transaction completion timestamp")
    location: Optional[Dict] = Field(None, description="Location data")
    
    # Computed fields
    total_value: Optional[float] = Field(None, description="Total transaction value")
    price_vs_market: Optional[str] = Field(None, description="Price comparison to market")
    
    class Config:
        from_attributes = True


class TransactionHistoryResponse(BaseModel):
    """Response containing transaction history"""
    transactions: List[TransactionResponse] = Field(..., description="List of transactions")
    total: int = Field(..., description="Total number of transactions")
    limit: Optional[int] = Field(None, description="Limit applied")
    offset: int = Field(default=0, description="Offset applied")


class VoiceTransactionHistoryResponse(BaseModel):
    """Response containing formatted transaction history for voice playback"""
    messages: List[str] = Field(..., description="Formatted messages for voice output")
    transaction_count: int = Field(..., description="Number of transactions")
    language: str = Field(..., description="Language code used for formatting")


class TransactionStatisticsResponse(BaseModel):
    """Response containing transaction statistics"""
    total_transactions: int = Field(..., description="Total number of transactions")
    total_as_buyer: int = Field(..., description="Transactions as buyer")
    total_as_seller: int = Field(..., description="Transactions as seller")
    commodities_traded: int = Field(..., description="Number of unique commodities")
    total_value_as_buyer: float = Field(..., description="Total value of purchases")
    total_value_as_seller: float = Field(..., description="Total value of sales")
    period_days: int = Field(..., description="Period covered in days")


class TransactionBetweenUsersResponse(BaseModel):
    """Response containing transactions between two users"""
    user1_id: str = Field(..., description="First user ID")
    user2_id: str = Field(..., description="Second user ID")
    transactions: List[TransactionResponse] = Field(..., description="List of transactions")
    total: int = Field(..., description="Total number of transactions")
