"""
Data Anonymization Service

This module provides utilities for anonymizing user data before sharing with
third parties for price aggregation and market intelligence.

Requirements: 15.3 - Data anonymization for third-party sharing
Property 48: Data Anonymization for Third Parties
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import hashlib
from pydantic import BaseModel, ConfigDict


class AnonymizedPriceData(BaseModel):
    """
    Anonymized price data suitable for third-party sharing.
    
    Contains only non-PII information needed for price aggregation:
    - Commodity information
    - Price and quantity
    - Coarse location (state/district only, no exact coordinates)
    - Timestamp
    - Anonymized user identifier (hashed)
    """
    commodity: str
    price: float
    quantity: float
    unit: str
    state: Optional[str] = None
    district: Optional[str] = None
    timestamp: datetime
    anonymized_user_id: str  # One-way hash of user ID
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class AnonymizedTransactionData(BaseModel):
    """
    Anonymized transaction data for market analysis.
    
    Contains aggregated transaction information without PII:
    - Commodity and pricing information
    - Coarse location data
    - Timestamp
    - Anonymized participant identifiers
    """
    commodity: str
    agreed_price: float
    quantity: float
    unit: str
    market_average_at_time: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    completed_at: datetime
    anonymized_buyer_id: str
    anonymized_seller_id: str
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DataAnonymizer:
    """
    Service for anonymizing user data before third-party sharing.
    
    This service removes all personally identifiable information (PII) from
    data that will be shared with third parties for price aggregation and
    market intelligence purposes.
    
    PII that is removed:
    - User names
    - Phone numbers
    - Exact locations (GPS coordinates, addresses)
    - User IDs (replaced with one-way hashes)
    - Voiceprint IDs
    - Any other identifying information
    
    Data that is preserved (for market intelligence):
    - Commodity information
    - Prices and quantities
    - Coarse location (state/district level only)
    - Timestamps
    - Anonymized user identifiers (for detecting patterns, not identification)
    
    Requirements: 15.3, 15.11
    """
    
    def __init__(self, salt: Optional[str] = None):
        """
        Initialize the data anonymizer.
        
        Args:
            salt: Optional salt for hashing user IDs. If not provided,
                  a default salt is used. In production, this should be
                  a secure random value stored in environment variables.
        """
        self.salt = salt or "multilingual-mandi-anonymization-salt-v1"
    
    def _hash_user_id(self, user_id: UUID) -> str:
        """
        Create a one-way hash of a user ID.
        
        This allows tracking patterns (e.g., repeat transactions) without
        being able to identify the actual user.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            A hexadecimal hash string
        """
        # Convert UUID to string and combine with salt
        data = f"{str(user_id)}{self.salt}"
        # Use SHA-256 for one-way hashing
        hash_obj = hashlib.sha256(data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _extract_coarse_location(self, location: Optional[Dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
        """
        Extract only coarse location data (state and district).
        
        Removes exact coordinates, addresses, and other precise location data.
        
        Args:
            location: Location dictionary that may contain various location fields
            
        Returns:
            Tuple of (state, district) or (None, None) if location is not available
        """
        if not location:
            return None, None
        
        state = location.get("state")
        district = location.get("district")
        
        return state, district
    
    def anonymize_transaction(
        self,
        transaction_data: Dict[str, Any]
    ) -> AnonymizedTransactionData:
        """
        Anonymize a transaction for third-party sharing.
        
        Removes all PII while preserving market intelligence data.
        
        Args:
            transaction_data: Dictionary containing transaction information with keys:
                - buyer_id: UUID of buyer
                - seller_id: UUID of seller
                - commodity: str
                - agreed_price: float
                - quantity: float
                - unit: str
                - market_average_at_time: Optional[float]
                - location: Optional[Dict]
                - completed_at: datetime
                
        Returns:
            AnonymizedTransactionData with PII removed
            
        Requirements: 15.3
        """
        # Extract coarse location
        state, district = self._extract_coarse_location(
            transaction_data.get("location")
        )
        
        # Create anonymized transaction
        return AnonymizedTransactionData(
            commodity=transaction_data["commodity"],
            agreed_price=transaction_data["agreed_price"],
            quantity=transaction_data["quantity"],
            unit=transaction_data["unit"],
            market_average_at_time=transaction_data.get("market_average_at_time"),
            state=state,
            district=district,
            completed_at=transaction_data["completed_at"],
            anonymized_buyer_id=self._hash_user_id(transaction_data["buyer_id"]),
            anonymized_seller_id=self._hash_user_id(transaction_data["seller_id"])
        )
    
    def anonymize_price_contribution(
        self,
        user_id: UUID,
        commodity: str,
        price: float,
        quantity: float,
        unit: str,
        location: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> AnonymizedPriceData:
        """
        Anonymize a user's price contribution for crowd-sourced price data.
        
        This is used when users contribute price information to the platform
        for aggregation and sharing with other users.
        
        Args:
            user_id: The user's UUID
            commodity: Commodity name
            price: Price per unit
            quantity: Quantity traded
            unit: Unit of measurement
            location: Optional location dictionary
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            AnonymizedPriceData with PII removed
            
        Requirements: 15.3
        """
        # Extract coarse location
        state, district = self._extract_coarse_location(location)
        
        # Use current time if not provided
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create anonymized price data
        return AnonymizedPriceData(
            commodity=commodity,
            price=price,
            quantity=quantity,
            unit=unit,
            state=state,
            district=district,
            timestamp=timestamp,
            anonymized_user_id=self._hash_user_id(user_id)
        )
    
    def anonymize_bulk_transactions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[AnonymizedTransactionData]:
        """
        Anonymize multiple transactions in bulk.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of anonymized transactions
            
        Requirements: 15.3
        """
        return [
            self.anonymize_transaction(transaction)
            for transaction in transactions
        ]
    
    def anonymize_bulk_price_contributions(
        self,
        price_contributions: List[Dict[str, Any]]
    ) -> List[AnonymizedPriceData]:
        """
        Anonymize multiple price contributions in bulk.
        
        Args:
            price_contributions: List of price contribution dictionaries,
                each containing: user_id, commodity, price, quantity, unit,
                location (optional), timestamp (optional)
                
        Returns:
            List of anonymized price data
            
        Requirements: 15.3
        """
        return [
            self.anonymize_price_contribution(
                user_id=contrib["user_id"],
                commodity=contrib["commodity"],
                price=contrib["price"],
                quantity=contrib["quantity"],
                unit=contrib["unit"],
                location=contrib.get("location"),
                timestamp=contrib.get("timestamp")
            )
            for contrib in price_contributions
        ]
    
    def verify_no_pii(self, data: Dict[str, Any]) -> bool:
        """
        Verify that a data dictionary contains no PII.
        
        Checks for common PII fields that should not be present in
        anonymized data.
        
        Args:
            data: Dictionary to check
            
        Returns:
            True if no PII detected, False otherwise
        """
        # List of PII field names that should not be present
        pii_fields = {
            "name", "phone_number", "phone", "email", "address",
            "user_id", "buyer_id", "seller_id", "voiceprint_id",
            "latitude", "longitude", "coordinates", "gps",
            "street", "house_number", "postal_code", "zip_code"
        }
        
        # Check if any PII fields are present
        data_keys = set(data.keys())
        found_pii = data_keys.intersection(pii_fields)
        
        if found_pii:
            return False
        
        # Check nested dictionaries
        for value in data.values():
            if isinstance(value, dict):
                if not self.verify_no_pii(value):
                    return False
        
        return True
