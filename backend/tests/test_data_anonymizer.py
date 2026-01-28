"""
Unit tests for Data Anonymization Service

Tests the anonymization of user data before third-party sharing.

Requirements: 15.3 - Data anonymization for third-party sharing
"""
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from app.services.privacy.data_anonymizer import (
    DataAnonymizer,
    AnonymizedPriceData,
    AnonymizedTransactionData
)


@pytest.fixture
def anonymizer():
    """Create a DataAnonymizer instance with a test salt"""
    return DataAnonymizer(salt="test-salt-12345")


@pytest.fixture
def sample_transaction():
    """Create a sample transaction with PII"""
    return {
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
            "latitude": 18.5204,
            "longitude": 73.8567,
            "address": "123 Market Street"
        },
        "completed_at": datetime(2024, 1, 15, 10, 30, 0)
    }


@pytest.fixture
def sample_price_contribution():
    """Create a sample price contribution with PII"""
    return {
        "user_id": uuid4(),
        "commodity": "onion",
        "price": 30.00,
        "quantity": 50.0,
        "unit": "kg",
        "location": {
            "state": "Karnataka",
            "district": "Bangalore",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "street": "MG Road"
        },
        "timestamp": datetime(2024, 1, 15, 14, 0, 0)
    }


class TestDataAnonymizer:
    """Test suite for DataAnonymizer"""
    
    def test_initialization_with_custom_salt(self):
        """Test that anonymizer can be initialized with custom salt"""
        custom_salt = "my-custom-salt"
        anonymizer = DataAnonymizer(salt=custom_salt)
        assert anonymizer.salt == custom_salt
    
    def test_initialization_with_default_salt(self):
        """Test that anonymizer uses default salt when none provided"""
        anonymizer = DataAnonymizer()
        assert anonymizer.salt is not None
        assert len(anonymizer.salt) > 0
    
    def test_hash_user_id_is_deterministic(self, anonymizer):
        """Test that hashing the same user ID produces the same hash"""
        user_id = uuid4()
        hash1 = anonymizer._hash_user_id(user_id)
        hash2 = anonymizer._hash_user_id(user_id)
        assert hash1 == hash2
    
    def test_hash_user_id_different_for_different_users(self, anonymizer):
        """Test that different user IDs produce different hashes"""
        user_id1 = uuid4()
        user_id2 = uuid4()
        hash1 = anonymizer._hash_user_id(user_id1)
        hash2 = anonymizer._hash_user_id(user_id2)
        assert hash1 != hash2
    
    def test_hash_user_id_is_one_way(self, anonymizer):
        """Test that hash cannot be reversed to get original user ID"""
        user_id = uuid4()
        hashed = anonymizer._hash_user_id(user_id)
        # Hash should be a hex string
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 produces 64 hex characters
        # Should not contain the original UUID
        assert str(user_id) not in hashed
    
    def test_extract_coarse_location_with_full_data(self, anonymizer):
        """Test extracting state and district from location with all fields"""
        location = {
            "state": "Maharashtra",
            "district": "Pune",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "address": "123 Market Street"
        }
        state, district = anonymizer._extract_coarse_location(location)
        assert state == "Maharashtra"
        assert district == "Pune"
    
    def test_extract_coarse_location_with_minimal_data(self, anonymizer):
        """Test extracting location when only state is available"""
        location = {"state": "Karnataka"}
        state, district = anonymizer._extract_coarse_location(location)
        assert state == "Karnataka"
        assert district is None
    
    def test_extract_coarse_location_with_none(self, anonymizer):
        """Test extracting location when location is None"""
        state, district = anonymizer._extract_coarse_location(None)
        assert state is None
        assert district is None
    
    def test_extract_coarse_location_with_empty_dict(self, anonymizer):
        """Test extracting location from empty dictionary"""
        state, district = anonymizer._extract_coarse_location({})
        assert state is None
        assert district is None


class TestTransactionAnonymization:
    """Test suite for transaction anonymization"""
    
    def test_anonymize_transaction_removes_pii(self, anonymizer, sample_transaction):
        """Test that transaction anonymization removes all PII"""
        anonymized = anonymizer.anonymize_transaction(sample_transaction)
        
        # Check that result is correct type
        assert isinstance(anonymized, AnonymizedTransactionData)
        
        # Check that commodity and price data is preserved
        assert anonymized.commodity == "tomato"
        assert anonymized.agreed_price == 25.50
        assert anonymized.quantity == 100.0
        assert anonymized.unit == "kg"
        assert anonymized.market_average_at_time == 24.00
        assert anonymized.completed_at == sample_transaction["completed_at"]
        
        # Check that coarse location is preserved
        assert anonymized.state == "Maharashtra"
        assert anonymized.district == "Pune"
        
        # Check that user IDs are hashed
        assert anonymized.anonymized_buyer_id != str(sample_transaction["buyer_id"])
        assert anonymized.anonymized_seller_id != str(sample_transaction["seller_id"])
        assert len(anonymized.anonymized_buyer_id) == 64  # SHA-256 hash
        assert len(anonymized.anonymized_seller_id) == 64
    
    def test_anonymize_transaction_without_location(self, anonymizer):
        """Test anonymizing transaction without location data"""
        transaction = {
            "buyer_id": uuid4(),
            "seller_id": uuid4(),
            "commodity": "wheat",
            "agreed_price": 35.00,
            "quantity": 200.0,
            "unit": "kg",
            "market_average_at_time": None,
            "location": None,
            "completed_at": datetime.utcnow()
        }
        
        anonymized = anonymizer.anonymize_transaction(transaction)
        
        assert anonymized.commodity == "wheat"
        assert anonymized.state is None
        assert anonymized.district is None
    
    def test_anonymize_transaction_preserves_market_data(self, anonymizer, sample_transaction):
        """Test that market average data is preserved"""
        anonymized = anonymizer.anonymize_transaction(sample_transaction)
        assert anonymized.market_average_at_time == 24.00
    
    def test_anonymize_bulk_transactions(self, anonymizer):
        """Test anonymizing multiple transactions at once"""
        transactions = [
            {
                "buyer_id": uuid4(),
                "seller_id": uuid4(),
                "commodity": f"commodity_{i}",
                "agreed_price": 20.0 + i,
                "quantity": 100.0,
                "unit": "kg",
                "market_average_at_time": 20.0,
                "location": {"state": "Maharashtra", "district": "Pune"},
                "completed_at": datetime.utcnow()
            }
            for i in range(5)
        ]
        
        anonymized_list = anonymizer.anonymize_bulk_transactions(transactions)
        
        assert len(anonymized_list) == 5
        for i, anonymized in enumerate(anonymized_list):
            assert isinstance(anonymized, AnonymizedTransactionData)
            assert anonymized.commodity == f"commodity_{i}"
            assert anonymized.agreed_price == 20.0 + i


class TestPriceContributionAnonymization:
    """Test suite for price contribution anonymization"""
    
    def test_anonymize_price_contribution_removes_pii(self, anonymizer, sample_price_contribution):
        """Test that price contribution anonymization removes all PII"""
        anonymized = anonymizer.anonymize_price_contribution(
            user_id=sample_price_contribution["user_id"],
            commodity=sample_price_contribution["commodity"],
            price=sample_price_contribution["price"],
            quantity=sample_price_contribution["quantity"],
            unit=sample_price_contribution["unit"],
            location=sample_price_contribution["location"],
            timestamp=sample_price_contribution["timestamp"]
        )
        
        # Check that result is correct type
        assert isinstance(anonymized, AnonymizedPriceData)
        
        # Check that price data is preserved
        assert anonymized.commodity == "onion"
        assert anonymized.price == 30.00
        assert anonymized.quantity == 50.0
        assert anonymized.unit == "kg"
        assert anonymized.timestamp == sample_price_contribution["timestamp"]
        
        # Check that coarse location is preserved
        assert anonymized.state == "Karnataka"
        assert anonymized.district == "Bangalore"
        
        # Check that user ID is hashed
        assert anonymized.anonymized_user_id != str(sample_price_contribution["user_id"])
        assert len(anonymized.anonymized_user_id) == 64  # SHA-256 hash
    
    def test_anonymize_price_contribution_without_location(self, anonymizer):
        """Test anonymizing price contribution without location"""
        user_id = uuid4()
        anonymized = anonymizer.anonymize_price_contribution(
            user_id=user_id,
            commodity="rice",
            price=40.00,
            quantity=150.0,
            unit="kg",
            location=None,
            timestamp=datetime.utcnow()
        )
        
        assert anonymized.commodity == "rice"
        assert anonymized.state is None
        assert anonymized.district is None
    
    def test_anonymize_price_contribution_default_timestamp(self, anonymizer):
        """Test that default timestamp is used when not provided"""
        user_id = uuid4()
        before = datetime.utcnow()
        anonymized = anonymizer.anonymize_price_contribution(
            user_id=user_id,
            commodity="potato",
            price=18.00,
            quantity=75.0,
            unit="kg"
        )
        after = datetime.utcnow()
        
        # Timestamp should be between before and after
        assert before <= anonymized.timestamp <= after
    
    def test_anonymize_bulk_price_contributions(self, anonymizer):
        """Test anonymizing multiple price contributions at once"""
        contributions = [
            {
                "user_id": uuid4(),
                "commodity": f"commodity_{i}",
                "price": 25.0 + i,
                "quantity": 50.0,
                "unit": "kg",
                "location": {"state": "Karnataka", "district": "Bangalore"},
                "timestamp": datetime.utcnow()
            }
            for i in range(5)
        ]
        
        anonymized_list = anonymizer.anonymize_bulk_price_contributions(contributions)
        
        assert len(anonymized_list) == 5
        for i, anonymized in enumerate(anonymized_list):
            assert isinstance(anonymized, AnonymizedPriceData)
            assert anonymized.commodity == f"commodity_{i}"
            assert anonymized.price == 25.0 + i


class TestPIIVerification:
    """Test suite for PII verification"""
    
    def test_verify_no_pii_with_clean_data(self, anonymizer):
        """Test that clean data passes PII verification"""
        clean_data = {
            "commodity": "tomato",
            "price": 25.00,
            "quantity": 100.0,
            "state": "Maharashtra",
            "district": "Pune"
        }
        assert anonymizer.verify_no_pii(clean_data) is True
    
    def test_verify_no_pii_detects_user_id(self, anonymizer):
        """Test that user_id is detected as PII"""
        data_with_pii = {
            "commodity": "tomato",
            "price": 25.00,
            "user_id": str(uuid4())
        }
        assert anonymizer.verify_no_pii(data_with_pii) is False
    
    def test_verify_no_pii_detects_phone_number(self, anonymizer):
        """Test that phone_number is detected as PII"""
        data_with_pii = {
            "commodity": "tomato",
            "price": 25.00,
            "phone_number": "+91-9876543210"
        }
        assert anonymizer.verify_no_pii(data_with_pii) is False
    
    def test_verify_no_pii_detects_name(self, anonymizer):
        """Test that name is detected as PII"""
        data_with_pii = {
            "commodity": "tomato",
            "price": 25.00,
            "name": "John Doe"
        }
        assert anonymizer.verify_no_pii(data_with_pii) is False
    
    def test_verify_no_pii_detects_coordinates(self, anonymizer):
        """Test that GPS coordinates are detected as PII"""
        data_with_pii = {
            "commodity": "tomato",
            "price": 25.00,
            "latitude": 18.5204,
            "longitude": 73.8567
        }
        assert anonymizer.verify_no_pii(data_with_pii) is False
    
    def test_verify_no_pii_detects_nested_pii(self, anonymizer):
        """Test that PII in nested dictionaries is detected"""
        data_with_nested_pii = {
            "commodity": "tomato",
            "price": 25.00,
            "location": {
                "state": "Maharashtra",
                "phone_number": "+91-9876543210"
            }
        }
        assert anonymizer.verify_no_pii(data_with_nested_pii) is False
    
    def test_verify_no_pii_with_anonymized_transaction(self, anonymizer, sample_transaction):
        """Test that anonymized transaction passes PII verification"""
        anonymized = anonymizer.anonymize_transaction(sample_transaction)
        # Convert to dict for verification
        data_dict = anonymized.model_dump()
        assert anonymizer.verify_no_pii(data_dict) is True
    
    def test_verify_no_pii_with_anonymized_price_data(self, anonymizer):
        """Test that anonymized price data passes PII verification"""
        anonymized = anonymizer.anonymize_price_contribution(
            user_id=uuid4(),
            commodity="wheat",
            price=35.00,
            quantity=100.0,
            unit="kg",
            location={"state": "Maharashtra", "district": "Pune"}
        )
        # Convert to dict for verification
        data_dict = anonymized.model_dump()
        assert anonymizer.verify_no_pii(data_dict) is True


class TestAnonymizationConsistency:
    """Test suite for anonymization consistency"""
    
    def test_same_user_produces_same_hash(self, anonymizer):
        """Test that the same user always gets the same anonymized ID"""
        user_id = uuid4()
        
        # Create two price contributions from the same user
        contrib1 = anonymizer.anonymize_price_contribution(
            user_id=user_id,
            commodity="tomato",
            price=25.00,
            quantity=100.0,
            unit="kg"
        )
        
        contrib2 = anonymizer.anonymize_price_contribution(
            user_id=user_id,
            commodity="onion",
            price=30.00,
            quantity=50.0,
            unit="kg"
        )
        
        # Both should have the same anonymized user ID
        assert contrib1.anonymized_user_id == contrib2.anonymized_user_id
    
    def test_different_users_produce_different_hashes(self, anonymizer):
        """Test that different users get different anonymized IDs"""
        user_id1 = uuid4()
        user_id2 = uuid4()
        
        contrib1 = anonymizer.anonymize_price_contribution(
            user_id=user_id1,
            commodity="tomato",
            price=25.00,
            quantity=100.0,
            unit="kg"
        )
        
        contrib2 = anonymizer.anonymize_price_contribution(
            user_id=user_id2,
            commodity="tomato",
            price=25.00,
            quantity=100.0,
            unit="kg"
        )
        
        # Different users should have different anonymized IDs
        assert contrib1.anonymized_user_id != contrib2.anonymized_user_id
    
    def test_different_salts_produce_different_hashes(self):
        """Test that different salts produce different hashes for same user"""
        user_id = uuid4()
        
        anonymizer1 = DataAnonymizer(salt="salt1")
        anonymizer2 = DataAnonymizer(salt="salt2")
        
        hash1 = anonymizer1._hash_user_id(user_id)
        hash2 = anonymizer2._hash_user_id(user_id)
        
        assert hash1 != hash2


class TestEdgeCases:
    """Test suite for edge cases"""
    
    def test_anonymize_transaction_with_zero_price(self, anonymizer):
        """Test anonymizing transaction with zero price"""
        transaction = {
            "buyer_id": uuid4(),
            "seller_id": uuid4(),
            "commodity": "sample",
            "agreed_price": 0.0,
            "quantity": 100.0,
            "unit": "kg",
            "market_average_at_time": 0.0,
            "location": None,
            "completed_at": datetime.utcnow()
        }
        
        anonymized = anonymizer.anonymize_transaction(transaction)
        assert anonymized.agreed_price == 0.0
    
    def test_anonymize_price_contribution_with_large_quantity(self, anonymizer):
        """Test anonymizing price contribution with very large quantity"""
        anonymized = anonymizer.anonymize_price_contribution(
            user_id=uuid4(),
            commodity="rice",
            price=35.00,
            quantity=1000000.0,
            unit="kg"
        )
        assert anonymized.quantity == 1000000.0
    
    def test_anonymize_transaction_with_special_characters_in_commodity(self, anonymizer):
        """Test anonymizing transaction with special characters in commodity name"""
        transaction = {
            "buyer_id": uuid4(),
            "seller_id": uuid4(),
            "commodity": "tomato (organic)",
            "agreed_price": 30.00,
            "quantity": 50.0,
            "unit": "kg",
            "market_average_at_time": 28.00,
            "location": {"state": "Maharashtra"},
            "completed_at": datetime.utcnow()
        }
        
        anonymized = anonymizer.anonymize_transaction(transaction)
        assert anonymized.commodity == "tomato (organic)"
