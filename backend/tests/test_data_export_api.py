"""
Unit tests for Data Export API endpoints

Tests the API endpoints for exporting anonymized data to third parties.

Requirements: 15.3 - Data anonymization for third-party sharing
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.dependencies import get_db
from app.models.base import Base
from app.models.transaction import Transaction


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_transactions():
    """Create sample transactions in the database"""
    db = TestingSessionLocal()
    
    transactions = []
    commodities = ["tomato", "onion", "potato"]
    
    for i in range(10):
        transaction = Transaction(
            id=uuid4(),
            buyer_id=uuid4(),
            seller_id=uuid4(),
            commodity=commodities[i % 3],
            quantity=100.0 + (i * 10),
            unit="kg",
            agreed_price=20.0 + (i * 2),
            market_average_at_time=20.0,
            conversation_id=uuid4(),
            completed_at=datetime.utcnow() - timedelta(days=i)
        )
        db.add(transaction)
        transactions.append(transaction)
    
    db.commit()
    db.close()
    
    return transactions


class TestDataExportAPI:
    """Test suite for data export API endpoints"""
    
    def test_health_check(self):
        """Test data export service health check"""
        response = client.get("/api/v1/data-export/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "data-export"
        assert data["anonymization"] == "enabled"
    
    def test_export_transactions_no_filters(self, sample_transactions):
        """Test exporting transactions without filters"""
        response = client.get("/api/v1/data-export/transactions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify anonymization
        for transaction in data:
            assert "commodity" in transaction
            assert "agreed_price" in transaction
            assert "quantity" in transaction
            assert "anonymized_buyer_id" in transaction
            assert "anonymized_seller_id" in transaction
            
            # Verify no PII
            assert "buyer_id" not in transaction
            assert "seller_id" not in transaction
            assert "name" not in transaction
            assert "phone_number" not in transaction
    
    def test_export_transactions_with_commodity_filter(self, sample_transactions):
        """Test exporting transactions filtered by commodity"""
        response = client.get("/api/v1/data-export/transactions?commodity=tomato")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All transactions should be for tomato
        for transaction in data:
            assert transaction["commodity"] == "tomato"
    
    def test_export_transactions_with_date_range(self, sample_transactions):
        """Test exporting transactions with date range filter"""
        start_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(
            f"/api/v1/data-export/transactions"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Verify all transactions are within date range
        for transaction in data:
            transaction_date = datetime.fromisoformat(
                transaction["completed_at"].replace("Z", "+00:00")
            )
            assert transaction_date >= datetime.fromisoformat(start_date)
            assert transaction_date <= datetime.fromisoformat(end_date)
    
    def test_export_transactions_with_limit(self, sample_transactions):
        """Test exporting transactions with limit"""
        response = client.get("/api/v1/data-export/transactions?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_export_transactions_limit_validation(self):
        """Test that limit parameter is validated"""
        # Test limit too high
        response = client.get("/api/v1/data-export/transactions?limit=20000")
        assert response.status_code == 422  # Validation error
        
        # Test limit too low
        response = client.get("/api/v1/data-export/transactions?limit=0")
        assert response.status_code == 422  # Validation error
    
    def test_export_price_contributions_no_filters(self, sample_transactions):
        """Test exporting price contributions without filters"""
        response = client.get("/api/v1/data-export/price-contributions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify anonymization
        for contribution in data:
            assert "commodity" in contribution
            assert "price" in contribution
            assert "quantity" in contribution
            assert "anonymized_user_id" in contribution
            
            # Verify no PII
            assert "user_id" not in contribution
            assert "name" not in contribution
            assert "phone_number" not in contribution
    
    def test_export_price_contributions_with_commodity_filter(self, sample_transactions):
        """Test exporting price contributions filtered by commodity"""
        response = client.get(
            "/api/v1/data-export/price-contributions?commodity=onion"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All contributions should be for onion
        for contribution in data:
            assert contribution["commodity"] == "onion"
    
    def test_export_price_contributions_with_date_range(self, sample_transactions):
        """Test exporting price contributions with date range"""
        start_date = (datetime.utcnow() - timedelta(days=3)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = client.get(
            f"/api/v1/data-export/price-contributions"
            f"?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_market_statistics_success(self, sample_transactions):
        """Test getting market statistics"""
        response = client.get("/api/v1/data-export/market-statistics?commodity=tomato")
        assert response.status_code == 200
        
        data = response.json()
        assert data["commodity"] == "tomato"
        assert "sample_size" in data
        assert "price_statistics" in data
        assert "quantity_statistics" in data
        
        # Verify price statistics
        price_stats = data["price_statistics"]
        assert "min" in price_stats
        assert "max" in price_stats
        assert "average" in price_stats
        assert "median" in price_stats
        assert "std_dev" in price_stats
        
        # Verify quantity statistics
        quantity_stats = data["quantity_statistics"]
        assert "total" in quantity_stats
        assert "average" in quantity_stats
        assert "median" in quantity_stats
    
    def test_market_statistics_with_days_filter(self, sample_transactions):
        """Test market statistics with custom days parameter"""
        response = client.get(
            "/api/v1/data-export/market-statistics?commodity=potato&days=3"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["commodity"] == "potato"
        assert data["period_days"] == 3
    
    def test_market_statistics_no_data(self):
        """Test market statistics when no data is available"""
        response = client.get(
            "/api/v1/data-export/market-statistics?commodity=nonexistent"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["sample_size"] == 0
        assert "message" in data
    
    def test_market_statistics_missing_commodity(self):
        """Test market statistics without commodity parameter"""
        response = client.get("/api/v1/data-export/market-statistics")
        assert response.status_code == 422  # Validation error
    
    def test_market_statistics_days_validation(self):
        """Test that days parameter is validated"""
        # Test days too high
        response = client.get(
            "/api/v1/data-export/market-statistics?commodity=tomato&days=100"
        )
        assert response.status_code == 422  # Validation error
        
        # Test days too low
        response = client.get(
            "/api/v1/data-export/market-statistics?commodity=tomato&days=0"
        )
        assert response.status_code == 422  # Validation error


class TestDataAnonymizationInAPI:
    """Test that API properly anonymizes data"""
    
    def test_transaction_export_removes_all_pii(self, sample_transactions):
        """Test that exported transactions contain no PII"""
        response = client.get("/api/v1/data-export/transactions")
        assert response.status_code == 200
        
        data = response.json()
        
        # List of PII fields that should NOT be present
        pii_fields = [
            "buyer_id", "seller_id", "user_id",
            "name", "phone_number", "phone", "email",
            "address", "latitude", "longitude",
            "voiceprint_id", "coordinates"
        ]
        
        for transaction in data:
            for pii_field in pii_fields:
                assert pii_field not in transaction, \
                    f"PII field '{pii_field}' found in transaction"
    
    def test_price_contribution_export_removes_all_pii(self, sample_transactions):
        """Test that exported price contributions contain no PII"""
        response = client.get("/api/v1/data-export/price-contributions")
        assert response.status_code == 200
        
        data = response.json()
        
        # List of PII fields that should NOT be present
        pii_fields = [
            "user_id", "buyer_id", "seller_id",
            "name", "phone_number", "phone", "email",
            "address", "latitude", "longitude",
            "voiceprint_id", "coordinates"
        ]
        
        for contribution in data:
            for pii_field in pii_fields:
                assert pii_field not in contribution, \
                    f"PII field '{pii_field}' found in price contribution"
    
    def test_anonymized_ids_are_consistent(self, sample_transactions):
        """Test that same user gets same anonymized ID across exports"""
        # Export transactions twice
        response1 = client.get("/api/v1/data-export/transactions?limit=5")
        response2 = client.get("/api/v1/data-export/transactions?limit=5")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Compare anonymized IDs for same transactions
        for i in range(min(len(data1), len(data2))):
            assert data1[i]["anonymized_buyer_id"] == data2[i]["anonymized_buyer_id"]
            assert data1[i]["anonymized_seller_id"] == data2[i]["anonymized_seller_id"]
    
    def test_market_statistics_contain_no_individual_data(self, sample_transactions):
        """Test that market statistics contain only aggregates, no individual data"""
        response = client.get(
            "/api/v1/data-export/market-statistics?commodity=tomato"
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Should only contain aggregate statistics
        assert "price_statistics" in data
        assert "quantity_statistics" in data
        
        # Should NOT contain individual transaction data
        assert "transactions" not in data
        assert "users" not in data
        
        # Should NOT contain any IDs
        pii_fields = ["user_id", "buyer_id", "seller_id", "transaction_id"]
        for pii_field in pii_fields:
            assert pii_field not in data


class TestDataExportEdgeCases:
    """Test edge cases for data export API"""
    
    def test_export_with_no_transactions(self):
        """Test exporting when database is empty"""
        response = client.get("/api/v1/data-export/transactions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_export_with_invalid_date_format(self):
        """Test exporting with invalid date format"""
        response = client.get(
            "/api/v1/data-export/transactions?start_date=invalid-date"
        )
        assert response.status_code == 422  # Validation error
    
    def test_market_statistics_with_single_transaction(self):
        """Test market statistics with only one transaction"""
        db = TestingSessionLocal()
        
        transaction = Transaction(
            id=uuid4(),
            buyer_id=uuid4(),
            seller_id=uuid4(),
            commodity="single-item",
            quantity=100.0,
            unit="kg",
            agreed_price=25.0,
            market_average_at_time=24.0,
            conversation_id=uuid4(),
            completed_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        db.close()
        
        response = client.get(
            "/api/v1/data-export/market-statistics?commodity=single-item"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["sample_size"] == 1
        assert data["price_statistics"]["std_dev"] == 0.0  # No deviation with 1 sample
