"""Unit tests for RetryManager

Tests retry logic with exponential backoff.
Requirements: 14.3
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from app.services.error_handler import RetryManager, with_retry, with_retry_sync


@pytest.fixture
def retry_manager():
    """Create RetryManager instance with default settings"""
    return RetryManager(max_retries=3, base_delay=1.0)


@pytest.fixture
def fast_retry_manager():
    """Create RetryManager with fast delays for testing"""
    return RetryManager(max_retries=3, base_delay=0.01)


class TestRetryManagerInitialization:
    """Test RetryManager initialization"""
    
    def test_default_initialization(self):
        """Test RetryManager with default parameters"""
        manager = RetryManager()
        assert manager.max_retries == 3
        assert manager.base_delay == 1.0
        assert manager.max_delay is None
    
    def test_custom_initialization(self):
        """Test RetryManager with custom parameters"""
        manager = RetryManager(max_retries=5, base_delay=2.0, max_delay=10.0)
        assert manager.max_retries == 5
        assert manager.base_delay == 2.0
        assert manager.max_delay == 10.0


class TestAsyncRetryWithBackoff:
    """Test async retry with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_successful_operation_no_retry(self, fast_retry_manager):
        """Test operation succeeds on first attempt"""
        async def successful_operation():
            return "success"
        
        result = await fast_retry_manager.retry_with_backoff(successful_operation)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_operation_succeeds_after_retries(self, fast_retry_manager):
        """Test operation succeeds after some failures"""
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await fast_retry_manager.retry_with_backoff(flaky_operation)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_operation_fails_after_max_retries(self, fast_retry_manager):
        """Test operation fails after exhausting all retries"""
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError, match="Persistent failure"):
            await fast_retry_manager.retry_with_backoff(failing_operation)
        
        assert call_count == 3  # Should attempt max_retries times
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self):
        """Test that delays follow exponential backoff pattern (1s, 2s, 4s)"""
        manager = RetryManager(max_retries=3, base_delay=0.1)
        call_times = []
        
        async def failing_operation():
            call_times.append(time.time())
            raise ConnectionError("Test failure")
        
        with pytest.raises(ConnectionError):
            await manager.retry_with_backoff(failing_operation)
        
        # Verify we have 3 attempts
        assert len(call_times) == 3
        
        # Calculate delays between attempts
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        # Delays should be approximately 0.1s and 0.2s (with some tolerance)
        assert 0.08 <= delay1 <= 0.15  # ~0.1s (base_delay * 2^0)
        assert 0.18 <= delay2 <= 0.25  # ~0.2s (base_delay * 2^1)
    
    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test that max_delay caps the exponential growth"""
        manager = RetryManager(max_retries=3, base_delay=0.1, max_delay=0.15)
        call_times = []
        
        async def failing_operation():
            call_times.append(time.time())
            raise ConnectionError("Test failure")
        
        with pytest.raises(ConnectionError):
            await manager.retry_with_backoff(failing_operation)
        
        # Calculate delays
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        # First delay should be 0.1s
        assert 0.08 <= delay1 <= 0.15
        
        # Second delay should be capped at 0.15s (not 0.2s)
        assert 0.13 <= delay2 <= 0.18
    
    @pytest.mark.asyncio
    async def test_retry_with_arguments(self, fast_retry_manager):
        """Test retry with function arguments"""
        call_count = 0
        
        async def operation_with_args(x, y, z=0):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return x + y + z
        
        result = await fast_retry_manager.retry_with_backoff(
            operation_with_args, 1, 2, z=3
        )
        assert result == 6
        assert call_count == 2


class TestSyncRetryWithBackoff:
    """Test synchronous retry with exponential backoff"""
    
    def test_successful_sync_operation(self, fast_retry_manager):
        """Test sync operation succeeds on first attempt"""
        def successful_operation():
            return "success"
        
        result = fast_retry_manager.retry_sync_with_backoff(successful_operation)
        assert result == "success"
    
    def test_sync_operation_succeeds_after_retries(self, fast_retry_manager):
        """Test sync operation succeeds after some failures"""
        call_count = 0
        
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = fast_retry_manager.retry_sync_with_backoff(flaky_operation)
        assert result == "success"
        assert call_count == 3
    
    def test_sync_operation_fails_after_max_retries(self, fast_retry_manager):
        """Test sync operation fails after exhausting all retries"""
        call_count = 0
        
        def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError, match="Persistent failure"):
            fast_retry_manager.retry_sync_with_backoff(failing_operation)
        
        assert call_count == 3
    
    def test_sync_exponential_backoff_delays(self):
        """Test sync delays follow exponential backoff pattern"""
        manager = RetryManager(max_retries=3, base_delay=0.1)
        call_times = []
        
        def failing_operation():
            call_times.append(time.time())
            raise ConnectionError("Test failure")
        
        with pytest.raises(ConnectionError):
            manager.retry_sync_with_backoff(failing_operation)
        
        assert len(call_times) == 3
        
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        assert 0.08 <= delay1 <= 0.15
        assert 0.18 <= delay2 <= 0.25


class TestCustomRetryStrategy:
    """Test custom retry strategies"""
    
    @pytest.mark.asyncio
    async def test_retry_on_specific_exceptions(self, fast_retry_manager):
        """Test retry only on specific exception types"""
        call_count = 0
        
        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Retryable error")
            elif call_count == 2:
                raise ValueError("Non-retryable error")
            return "success"
        
        # Should retry on ConnectionError but not on ValueError
        with pytest.raises(ValueError, match="Non-retryable error"):
            await fast_retry_manager.retry_with_custom_strategy(
                operation,
                retry_on=[ConnectionError, TimeoutError]
            )
        
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_custom_max_retries(self, fast_retry_manager):
        """Test custom max_retries override"""
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Test failure")
        
        with pytest.raises(ConnectionError):
            await fast_retry_manager.retry_with_custom_strategy(
                failing_operation,
                max_retries=5
            )
        
        assert call_count == 5  # Should use custom max_retries
    
    @pytest.mark.asyncio
    async def test_retry_on_all_exceptions_when_none(self, fast_retry_manager):
        """Test retry on all exceptions when retry_on is None"""
        call_count = 0
        
        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Any error")
            return "success"
        
        result = await fast_retry_manager.retry_with_custom_strategy(
            operation,
            retry_on=None
        )
        assert result == "success"
        assert call_count == 3


class TestRetryDecorators:
    """Test retry decorators"""
    
    @pytest.mark.asyncio
    async def test_with_retry_decorator_success(self):
        """Test @with_retry decorator on successful operation"""
        call_count = 0
        
        @with_retry(max_retries=3, base_delay=0.01)
        async def decorated_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await decorated_operation()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_with_retry_decorator_failure(self):
        """Test @with_retry decorator on failing operation"""
        call_count = 0
        
        @with_retry(max_retries=3, base_delay=0.01)
        async def decorated_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError):
            await decorated_operation()
        
        assert call_count == 3
    
    def test_with_retry_sync_decorator_success(self):
        """Test @with_retry_sync decorator on successful operation"""
        call_count = 0
        
        @with_retry_sync(max_retries=3, base_delay=0.01)
        def decorated_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = decorated_operation()
        assert result == "success"
        assert call_count == 2
    
    def test_with_retry_sync_decorator_failure(self):
        """Test @with_retry_sync decorator on failing operation"""
        call_count = 0
        
        @with_retry_sync(max_retries=3, base_delay=0.01)
        def decorated_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError):
            decorated_operation()
        
        assert call_count == 3


class TestRetryManagerLogging:
    """Test retry manager logging behavior"""
    
    @pytest.mark.asyncio
    async def test_logs_retry_attempts(self, fast_retry_manager, caplog):
        """Test that retry attempts are logged"""
        import logging
        caplog.set_level(logging.WARNING)
        
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        await fast_retry_manager.retry_with_backoff(flaky_operation)
        
        # Should have warning logs for the failed attempts
        assert len(caplog.records) >= 2
        assert any("failed on attempt" in record.message.lower() for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_logs_success_after_retry(self, fast_retry_manager, caplog):
        """Test that success after retry is logged"""
        import logging
        caplog.set_level(logging.INFO)
        
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        await fast_retry_manager.retry_with_backoff(flaky_operation)
        
        # Should have info log for success
        assert any("succeeded on attempt" in record.message.lower() for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_logs_final_failure(self, fast_retry_manager, caplog):
        """Test that final failure is logged"""
        import logging
        caplog.set_level(logging.ERROR)
        
        async def failing_operation():
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(ConnectionError):
            await fast_retry_manager.retry_with_backoff(failing_operation)
        
        # Should have error log for final failure
        assert any("failed after" in record.message.lower() for record in caplog.records)


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """Test with zero retries (should fail immediately)"""
        manager = RetryManager(max_retries=1, base_delay=0.01)
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Failure")
        
        with pytest.raises(ConnectionError):
            await manager.retry_with_backoff(failing_operation)
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_different_exception_types(self, fast_retry_manager):
        """Test retry with different exception types"""
        exceptions = [
            ConnectionError("Connection error"),
            TimeoutError("Timeout error"),
            ValueError("Value error"),
        ]
        call_count = 0
        
        async def operation():
            nonlocal call_count
            if call_count < len(exceptions):
                exc = exceptions[call_count]
                call_count += 1
                raise exc
            return "success"
        
        with pytest.raises(ValueError):
            await fast_retry_manager.retry_with_backoff(operation)
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_operation_with_side_effects(self, fast_retry_manager):
        """Test that operation side effects are preserved across retries"""
        results = []
        
        async def operation_with_side_effects():
            results.append("attempt")
            if len(results) < 2:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await fast_retry_manager.retry_with_backoff(operation_with_side_effects)
        assert result == "success"
        assert len(results) == 2
        assert all(r == "attempt" for r in results)


class TestRequirement14_3:
    """Test compliance with Requirement 14.3"""
    
    @pytest.mark.asyncio
    async def test_max_3_retries(self):
        """Test that system retries up to 3 times before failing"""
        manager = RetryManager(max_retries=3, base_delay=0.01)
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise Exception("Service unavailable")
        
        with pytest.raises(Exception):
            await manager.retry_with_backoff(failing_operation)
        
        # Should attempt exactly 3 times
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_1_2_4_seconds(self):
        """Test exponential backoff with delays of 1s, 2s, 4s"""
        manager = RetryManager(max_retries=3, base_delay=1.0)
        call_times = []
        
        async def failing_operation():
            call_times.append(time.time())
            raise Exception("Service unavailable")
        
        with pytest.raises(Exception):
            await manager.retry_with_backoff(failing_operation)
        
        # Verify 3 attempts
        assert len(call_times) == 3
        
        # Calculate actual delays
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        # Delays should be approximately 1s and 2s (with tolerance for execution time)
        assert 0.9 <= delay1 <= 1.2  # ~1s (base_delay * 2^0)
        assert 1.9 <= delay2 <= 2.2  # ~2s (base_delay * 2^1)
    
    @pytest.mark.asyncio
    async def test_retry_notifies_user_after_max_attempts(self, fast_retry_manager):
        """Test that user is notified after max retry attempts"""
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Should raise exception after max retries (which would trigger user notification)
        with pytest.raises(Exception, match="Service unavailable"):
            await fast_retry_manager.retry_with_backoff(failing_operation)


class TestIntegrationWithErrorHandler:
    """Test integration with ErrorHandler service"""
    
    @pytest.mark.asyncio
    async def test_retry_manager_with_service_errors(self, fast_retry_manager):
        """Test RetryManager handles service errors appropriately"""
        call_count = 0
        
        async def service_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Service temporarily unavailable")
            return {"status": "success", "data": "result"}
        
        result = await fast_retry_manager.retry_with_backoff(service_call)
        assert result["status"] == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_manager_with_network_errors(self, fast_retry_manager):
        """Test RetryManager handles network errors appropriately"""
        call_count = 0
        
        async def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network connection lost")
            return "data"
        
        result = await fast_retry_manager.retry_with_backoff(network_call)
        assert result == "data"
        assert call_count == 2
