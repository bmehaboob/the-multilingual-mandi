"""
Tests for Price API endpoints

Tests price query and comparison functionality.
Requirements: 6.3, 7.5
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestPriceAPI:
    """Test suite for price API endpoints"""
    
    def test_query_price_success(self):
        """Test successful price query"""
        response = client.post(
            "/api/v1/prices/query",
            json={
                "commodity": "tomato",
                "state": "Maharashtra"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "commodity" in data
        assert "location" in data
        assert "min_price" in data
        assert "max_price" in data
        assert "average_price" in data
        assert "sources_used" in data
        
        # Verify data values
        assert data["commodity"] == "tomato"
        assert data["location"]["state"] == "Maharashtra"
        assert data["min_price"] > 0
        assert data["max_price"] > 0
        assert data["average_price"] > 0
        assert len(data["sources_used"]) > 0
    
    def test_query_price_without_state(self):
        """Test price query without state (should default to Maharashtra)"""
        response = client.post(
            "/api/v1/prices/query",
            json={
                "commodity": "onion"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["location"]["state"] == "Maharashtra"
    
    def test_compare_price_fair(self):
        """Test price comparison with fair price"""
        response = client.post(
            "/api/v1/prices/compare",
            json={
                "commodity": "tomato",
                "quoted_price": 20.0,
                "state": "Maharashtra"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "verdict" in data
        assert "message" in data
        assert "percentage_difference" in data
        assert "market_average" in data
        assert "quoted_price" in data
        assert "market_data" in data
        
        # Verify verdict is one of the expected values
        assert data["verdict"] in ["fair", "high", "low", "slightly_high", "slightly_low"]
    
    def test_compare_price_high(self):
        """Test price comparison with high price"""
        response = client.post(
            "/api/v1/prices/compare",
            json={
                "commodity": "tomato",
                "quoted_price": 100.0,  # Very high price
                "state": "Maharashtra"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be classified as high
        assert data["verdict"] in ["high", "slightly_high"]
        assert data["percentage_difference"] > 0
    
    def test_compare_price_low(self):
        """Test price comparison with low price"""
        response = client.post(
            "/api/v1/prices/compare",
            json={
                "commodity": "tomato",
                "quoted_price": 5.0,  # Very low price
                "state": "Maharashtra"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be classified as low
        assert data["verdict"] in ["low", "slightly_low"]
        assert data["percentage_difference"] < 0
    
    def test_list_commodities(self):
        """Test listing available commodities"""
        response = client.get("/api/v1/prices/commodities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "commodities" in data
        assert "count" in data
        assert isinstance(data["commodities"], list)
        assert len(data["commodities"]) > 0
        assert data["count"] == len(data["commodities"])
        
        # Verify some common commodities are present
        commodities = data["commodities"]
        assert "tomato" in commodities
        assert "onion" in commodities
        assert "rice" in commodities
    
    def test_query_price_response_time(self):
        """Test that price query responds within 3 seconds (Requirement 6.3)"""
        import time
        
        start_time = time.time()
        response = client.post(
            "/api/v1/prices/query",
            json={
                "commodity": "tomato",
                "state": "Maharashtra"
            }
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 3.0, f"Response time {response_time}s exceeds 3 second requirement"
    
    def test_data_source_indicators(self):
        """Test that data sources are clearly indicated (Requirement 7.5)"""
        response = client.post(
            "/api/v1/prices/query",
            json={
                "commodity": "tomato",
                "state": "Maharashtra"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sources_used is present and contains valid sources
        assert "sources_used" in data
        assert len(data["sources_used"]) > 0
        
        valid_sources = ["enam", "mandi_board", "crowd_sourced", "demo"]
        for source in data["sources_used"]:
            assert source in valid_sources, f"Invalid source: {source}"
