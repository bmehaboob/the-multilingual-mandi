"""Unit tests for graceful degradation manager

Tests cover:
- Service health tracking
- Failure recording and recovery
- Fallback execution
- System health reporting
- Available features tracking

Requirements: 14.5
"""
import pytest
import asyncio
from datetime import datetime
from backend.app.services.error_handler.graceful_degradation import (
    GracefulDegradationManager,
    ServiceType,
    ServiceStatus,
    ServiceHealth,
    DegradedModeConfig,
)


class TestGracefulDegradationManager:
    """Test suite for GracefulDegradationManager"""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test"""
        config = DegradedModeConfig(
            max_failures=3,
            failure_window=300,
            retry_interval=60,
            auto_fallback=True
        )
        return GracefulDegradationManager(config)
    
    def test_initialization(self, manager):
        """Test that manager initializes with all services healthy"""
        for service_type in ServiceType:
            status = manager.get_service_status(service_type)
            assert status == ServiceStatus.HEALTHY
            assert manager.is_service_available(service_type)
    
    def test_service_has_fallback(self, manager):
        """Test that services with fallbacks are correctly identified"""
        # Services that should have fallbacks
        assert manager.has_fallback(ServiceType.STT)
        assert manager.has_fallback(ServiceType.TRANSLATION)
        assert manager.has_fallback(ServiceType.TTS)
        assert manager.has_fallback(ServiceType.LLM)
        assert manager.has_fallback(ServiceType.PRICE_ORACLE)
        assert manager.has_fallback(ServiceType.VOICE_BIOMETRIC)
        assert manager.has_fallback(ServiceType.CACHE)
    
    @pytest.mark.asyncio
    async def test_record_single_failure(self, manager):
        """Test recording a single service failure"""
        error = Exception("Test error")
        
        await manager.record_service_failure(ServiceType.STT, error)
        
        health = manager.service_health[ServiceType.STT]
        assert health.failure_count == 1
        assert health.status == ServiceStatus.DEGRADED
        assert health.last_error == "Test error"
        assert manager.is_service_available(ServiceType.STT)
    
    @pytest.mark.asyncio
    async def test_record_multiple_failures_to_unavailable(self, manager):
        """Test that multiple failures mark service as unavailable"""
        error = Exception("Test error")
        
        # Record failures up to max_failures
        for i in range(manager.config.max_failures):
            await manager.record_service_failure(ServiceType.STT, error)
        
        health = manager.service_health[ServiceType.STT]
        assert health.failure_count == manager.config.max_failures
        assert health.status == ServiceStatus.UNAVAILABLE
        assert not manager.is_service_available(ServiceType.STT)
    
    @pytest.mark.asyncio
    async def test_service_recovery(self, manager):
        """Test that service recovers after successful call"""
        error = Exception("Test error")
        
        # Record some failures
        await manager.record_service_failure(ServiceType.STT, error)
        await manager.record_service_failure(ServiceType.STT, error)
        
        assert manager.service_health[ServiceType.STT].failure_count == 2
        assert manager.service_health[ServiceType.STT].status == ServiceStatus.DEGRADED
        
        # Record success
        await manager.record_service_success(ServiceType.STT)
        
        health = manager.service_health[ServiceType.STT]
        assert health.failure_count == 0
        assert health.status == ServiceStatus.HEALTHY
        assert health.last_error is None
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self, manager):
        """Test successful execution without fallback"""
        async def primary_operation(value):
            return value * 2
        
        result = await manager.execute_with_fallback(
            ServiceType.STT,
            primary_operation,
            5
        )
        
        assert result == 10
        assert manager.get_service_status(ServiceType.STT) == ServiceStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_on_failure(self, manager):
        """Test fallback execution when primary fails"""
        async def primary_operation(value):
            raise Exception("Primary failed")
        
        async def fallback_handler(value):
            return value * 3  # Different behavior for fallback
        
        # Register fallback
        manager.register_fallback_handler(ServiceType.STT, fallback_handler)
        
        result = await manager.execute_with_fallback(
            ServiceType.STT,
            primary_operation,
            5
        )
        
        assert result == 15  # Fallback result
        assert manager.service_health[ServiceType.STT].failure_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_no_handler(self, manager):
        """Test that exception is raised when no fallback handler exists"""
        async def primary_operation():
            raise Exception("Primary failed")
        
        # Don't register a fallback handler
        # When auto_fallback is enabled but no handler is registered,
        # it should raise ValueError about missing handler
        
        with pytest.raises(ValueError, match="No fallback handler registered"):
            await manager.execute_with_fallback(
                ServiceType.STT,
                primary_operation
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_unavailable_service(self, manager):
        """Test that fallback is used when service is unavailable"""
        # Mark service as unavailable
        error = Exception("Service down")
        for _ in range(manager.config.max_failures):
            await manager.record_service_failure(ServiceType.STT, error)
        
        assert not manager.is_service_available(ServiceType.STT)
        
        # Register fallback
        async def fallback_handler(value):
            return f"fallback_{value}"
        
        manager.register_fallback_handler(ServiceType.STT, fallback_handler)
        
        # Primary operation should not be called
        async def primary_operation(value):
            raise AssertionError("Primary should not be called")
        
        result = await manager.execute_with_fallback(
            ServiceType.STT,
            primary_operation,
            "test"
        )
        
        assert result == "fallback_test"
    
    def test_get_system_health_all_healthy(self, manager):
        """Test system health when all services are healthy"""
        health = manager.get_system_health()
        
        assert health["overall_status"] == "healthy"
        assert health["healthy_services"] == len(ServiceType)
        assert health["degraded_services"] == 0
        assert health["unavailable_services"] == 0
        assert health["total_services"] == len(ServiceType)
    
    @pytest.mark.asyncio
    async def test_get_system_health_with_degraded(self, manager):
        """Test system health with degraded services"""
        error = Exception("Test error")
        await manager.record_service_failure(ServiceType.STT, error)
        
        health = manager.get_system_health()
        
        assert health["overall_status"] == "degraded"
        assert health["degraded_services"] == 1
        assert health["unavailable_services"] == 0
    
    @pytest.mark.asyncio
    async def test_get_system_health_with_unavailable(self, manager):
        """Test system health with unavailable services"""
        error = Exception("Test error")
        
        # Make STT unavailable
        for _ in range(manager.config.max_failures):
            await manager.record_service_failure(ServiceType.STT, error)
        
        health = manager.get_system_health()
        
        assert health["overall_status"] == "degraded"
        assert health["unavailable_services"] == 1
    
    @pytest.mark.asyncio
    async def test_get_system_health_critical_service_down(self, manager):
        """Test system health when critical service is down"""
        error = Exception("Database error")
        
        # Make database (critical service) unavailable
        for _ in range(manager.config.max_failures):
            await manager.record_service_failure(ServiceType.DATABASE, error)
        
        health = manager.get_system_health()
        
        assert health["overall_status"] == "critical"
        assert health["unavailable_services"] == 1
    
    def test_get_available_features_all_healthy(self, manager):
        """Test available features when all services are healthy"""
        features = manager.get_available_features()
        
        assert features["voice_input"] is True
        assert features["voice_output"] is True
        assert features["translation"] is True
        assert features["price_check"] is True
        assert features["negotiation_assistance"] is True
        assert features["voice_authentication"] is True
        assert features["data_persistence"] is True
        assert features["caching"] is True
    
    @pytest.mark.asyncio
    async def test_get_available_features_with_failures(self, manager):
        """Test available features when some services are down"""
        error = Exception("Test error")
        
        # Make STT unavailable
        for _ in range(manager.config.max_failures):
            await manager.record_service_failure(ServiceType.STT, error)
        
        # Make TTS unavailable
        for _ in range(manager.config.max_failures):
            await manager.record_service_failure(ServiceType.TTS, error)
        
        features = manager.get_available_features()
        
        assert features["voice_input"] is False
        assert features["voice_output"] is False
        assert features["translation"] is True  # Still available
        assert features["price_check"] is True  # Still available
    
    @pytest.mark.asyncio
    async def test_reset_service_health(self, manager):
        """Test manual service health reset"""
        error = Exception("Test error")
        
        # Make service degraded
        await manager.record_service_failure(ServiceType.STT, error)
        await manager.record_service_failure(ServiceType.STT, error)
        
        assert manager.service_health[ServiceType.STT].failure_count == 2
        assert manager.service_health[ServiceType.STT].status == ServiceStatus.DEGRADED
        
        # Reset
        await manager.reset_service_health(ServiceType.STT)
        
        health = manager.service_health[ServiceType.STT]
        assert health.failure_count == 0
        assert health.status == ServiceStatus.HEALTHY
        assert health.last_error is None
    
    @pytest.mark.asyncio
    async def test_concurrent_failure_recording(self, manager):
        """Test that concurrent failure recording is thread-safe"""
        error = Exception("Test error")
        
        # Record failures concurrently
        tasks = [
            manager.record_service_failure(ServiceType.STT, error)
            for _ in range(5)
        ]
        await asyncio.gather(*tasks)
        
        # Should have recorded all failures
        assert manager.service_health[ServiceType.STT].failure_count == 5
    
    def test_register_fallback_handler(self, manager):
        """Test registering a fallback handler"""
        def fallback_handler():
            return "fallback"
        
        manager.register_fallback_handler(ServiceType.STT, fallback_handler)
        
        assert ServiceType.STT in manager._fallback_handlers
        assert manager._fallback_handlers[ServiceType.STT] == fallback_handler
    
    @pytest.mark.asyncio
    async def test_fallback_with_sync_handler(self, manager):
        """Test fallback execution with synchronous handler"""
        async def primary_operation(value):
            raise Exception("Primary failed")
        
        def sync_fallback_handler(value):
            return value + 10
        
        manager.register_fallback_handler(ServiceType.STT, sync_fallback_handler)
        
        result = await manager.execute_with_fallback(
            ServiceType.STT,
            primary_operation,
            5
        )
        
        assert result == 15
    
    @pytest.mark.asyncio
    async def test_auto_fallback_disabled(self, manager):
        """Test that fallback is not used when auto_fallback is disabled"""
        manager.config.auto_fallback = False
        
        async def primary_operation():
            raise Exception("Primary failed")
        
        async def fallback_handler():
            return "fallback"
        
        manager.register_fallback_handler(ServiceType.STT, fallback_handler)
        
        with pytest.raises(Exception, match="Primary failed"):
            await manager.execute_with_fallback(
                ServiceType.STT,
                primary_operation
            )


class TestServiceHealth:
    """Test suite for ServiceHealth dataclass"""
    
    def test_service_health_creation(self):
        """Test creating a ServiceHealth instance"""
        health = ServiceHealth(
            service_type=ServiceType.STT,
            status=ServiceStatus.HEALTHY,
            last_check=datetime.now(),
            failure_count=0,
            fallback_available=True,
            fallback_description="Use cached data"
        )
        
        assert health.service_type == ServiceType.STT
        assert health.status == ServiceStatus.HEALTHY
        assert health.failure_count == 0
        assert health.fallback_available is True
    
    def test_service_health_to_dict(self):
        """Test converting ServiceHealth to dictionary"""
        now = datetime.now()
        health = ServiceHealth(
            service_type=ServiceType.STT,
            status=ServiceStatus.DEGRADED,
            last_check=now,
            failure_count=2,
            last_error="Test error",
            fallback_available=True,
            fallback_description="Use cached data"
        )
        
        result = health.to_dict()
        
        assert result["service_type"] == "stt"
        assert result["status"] == "degraded"
        assert result["failure_count"] == 2
        assert result["last_error"] == "Test error"
        assert result["fallback_available"] is True
        assert result["fallback_description"] == "Use cached data"


class TestDegradedModeConfig:
    """Test suite for DegradedModeConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = DegradedModeConfig()
        
        assert config.max_failures == 3
        assert config.failure_window == 300
        assert config.retry_interval == 60
        assert config.auto_fallback is True
        assert ServiceType.DATABASE in config.critical_services
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = DegradedModeConfig(
            max_failures=5,
            failure_window=600,
            retry_interval=120,
            auto_fallback=False
        )
        
        assert config.max_failures == 5
        assert config.failure_window == 600
        assert config.retry_interval == 120
        assert config.auto_fallback is False
    
    def test_services_with_fallbacks(self):
        """Test that all expected services have fallback descriptions"""
        config = DegradedModeConfig()
        
        assert ServiceType.STT in config.services_with_fallbacks
        assert ServiceType.TRANSLATION in config.services_with_fallbacks
        assert ServiceType.TTS in config.services_with_fallbacks
        assert ServiceType.LLM in config.services_with_fallbacks
        assert ServiceType.PRICE_ORACLE in config.services_with_fallbacks
        assert ServiceType.VOICE_BIOMETRIC in config.services_with_fallbacks
        assert ServiceType.CACHE in config.services_with_fallbacks


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_execute_fallback_without_registration(self, manager):
        """Test executing fallback without registered handler raises error"""
        with pytest.raises(ValueError, match="No fallback handler registered"):
            await manager._execute_fallback(ServiceType.STT, "test")
    
    @pytest.mark.asyncio
    async def test_multiple_service_failures_different_services(self, manager):
        """Test tracking failures across multiple services"""
        error = Exception("Test error")
        
        await manager.record_service_failure(ServiceType.STT, error)
        await manager.record_service_failure(ServiceType.TTS, error)
        await manager.record_service_failure(ServiceType.TRANSLATION, error)
        
        assert manager.service_health[ServiceType.STT].failure_count == 1
        assert manager.service_health[ServiceType.TTS].failure_count == 1
        assert manager.service_health[ServiceType.TRANSLATION].failure_count == 1
    
    @pytest.mark.asyncio
    async def test_fallback_handler_raises_exception(self, manager):
        """Test that exception in fallback handler is propagated"""
        async def primary_operation():
            raise Exception("Primary failed")
        
        async def fallback_handler():
            raise Exception("Fallback also failed")
        
        manager.register_fallback_handler(ServiceType.STT, fallback_handler)
        
        with pytest.raises(Exception, match="Fallback also failed"):
            await manager.execute_with_fallback(
                ServiceType.STT,
                primary_operation
            )


@pytest.fixture
def manager():
    """Fixture for creating a fresh manager"""
    return GracefulDegradationManager()
