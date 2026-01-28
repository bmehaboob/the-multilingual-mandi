"""Example usage of RetryManager with ErrorHandler

This example demonstrates how to use the RetryManager for handling
transient failures in service calls with exponential backoff.
"""
import asyncio
from app.services.error_handler import (
    RetryManager,
    ErrorHandler,
    ErrorContext,
    with_retry,
    with_retry_sync,
)


# Example 1: Basic async retry
async def example_basic_async_retry():
    """Example of basic async retry with exponential backoff"""
    print("\n=== Example 1: Basic Async Retry ===")
    
    retry_manager = RetryManager(max_retries=3, base_delay=1.0)
    
    # Simulate a flaky service that fails twice then succeeds
    attempt_count = 0
    
    async def flaky_service():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}")
        
        if attempt_count < 3:
            raise ConnectionError("Service temporarily unavailable")
        
        return {"status": "success", "data": "result"}
    
    try:
        result = await retry_manager.retry_with_backoff(flaky_service)
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Failed after all retries: {e}")


# Example 2: Sync retry
def example_sync_retry():
    """Example of synchronous retry"""
    print("\n=== Example 2: Sync Retry ===")
    
    retry_manager = RetryManager(max_retries=3, base_delay=0.5)
    
    attempt_count = 0
    
    def flaky_database_query():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Database query attempt {attempt_count}")
        
        if attempt_count < 2:
            raise Exception("Database connection timeout")
        
        return [{"id": 1, "name": "Item 1"}]
    
    try:
        result = retry_manager.retry_sync_with_backoff(flaky_database_query)
        print(f"Query successful! Results: {result}")
    except Exception as e:
        print(f"Query failed: {e}")


# Example 3: Using decorators
@with_retry(max_retries=3, base_delay=1.0)
async def fetch_external_data():
    """Example function with retry decorator"""
    print("Fetching external data...")
    # Simulate API call
    return {"data": "external_data"}


async def example_decorator():
    """Example of using retry decorator"""
    print("\n=== Example 3: Using Decorators ===")
    
    result = await fetch_external_data()
    print(f"Data fetched: {result}")


# Example 4: Custom retry strategy
async def example_custom_strategy():
    """Example of custom retry strategy"""
    print("\n=== Example 4: Custom Retry Strategy ===")
    
    retry_manager = RetryManager(max_retries=3, base_delay=0.5)
    
    attempt_count = 0
    
    async def service_with_different_errors():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}")
        
        if attempt_count == 1:
            raise ConnectionError("Network error - will retry")
        elif attempt_count == 2:
            raise ValueError("Validation error - won't retry")
        
        return "success"
    
    try:
        # Only retry on ConnectionError and TimeoutError
        result = await retry_manager.retry_with_custom_strategy(
            service_with_different_errors,
            retry_on=[ConnectionError, TimeoutError]
        )
        print(f"Result: {result}")
    except ValueError as e:
        print(f"Stopped retrying due to non-retryable error: {e}")


# Example 5: Integration with ErrorHandler
async def example_with_error_handler():
    """Example of RetryManager integrated with ErrorHandler"""
    print("\n=== Example 5: Integration with ErrorHandler ===")
    
    retry_manager = RetryManager(max_retries=3, base_delay=0.5)
    error_handler = ErrorHandler()
    
    async def external_service_call():
        # Simulate service failure
        raise Exception("Service unavailable")
    
    try:
        result = await retry_manager.retry_with_backoff(external_service_call)
        print(f"Service call successful: {result}")
    except Exception as e:
        # Handle error with ErrorHandler
        context = ErrorContext(
            user_language="en",
            operation="external_service_call"
        )
        error_response = error_handler.handle_error(e, context)
        
        print(f"Error Category: {error_response.category.value}")
        print(f"Error Message: {error_response.message}")
        print(f"Should Retry: {error_response.should_retry}")
        print(f"Corrective Actions:")
        for action in error_response.corrective_actions:
            print(f"  - {action.description} (Priority: {action.priority})")


# Example 6: Real-world scenario - Price API with retry
async def example_price_api_with_retry():
    """Example of using retry for price API calls"""
    print("\n=== Example 6: Price API with Retry ===")
    
    retry_manager = RetryManager(max_retries=3, base_delay=1.0)
    
    attempt_count = 0
    
    async def fetch_price_data(commodity: str):
        nonlocal attempt_count
        attempt_count += 1
        print(f"Fetching price for {commodity} (attempt {attempt_count})")
        
        # Simulate API failure on first attempt
        if attempt_count < 2:
            raise ConnectionError("eNAM API temporarily unavailable")
        
        # Return mock price data
        return {
            "commodity": commodity,
            "price": 25.50,
            "unit": "kg",
            "source": "eNAM",
            "timestamp": "2024-01-15T10:30:00"
        }
    
    try:
        price_data = await retry_manager.retry_with_backoff(
            fetch_price_data,
            "tomato"
        )
        print(f"Price data retrieved: {price_data}")
    except Exception as e:
        print(f"Failed to fetch price data: {e}")


# Example 7: Max delay cap
async def example_max_delay_cap():
    """Example showing max delay cap"""
    print("\n=== Example 7: Max Delay Cap ===")
    
    # Cap delays at 2 seconds even with exponential backoff
    retry_manager = RetryManager(max_retries=4, base_delay=1.0, max_delay=2.0)
    
    attempt_count = 0
    
    async def always_failing_service():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count} at {asyncio.get_event_loop().time():.2f}s")
        raise Exception("Service down")
    
    try:
        await retry_manager.retry_with_backoff(always_failing_service)
    except Exception:
        print(f"Failed after {attempt_count} attempts")
        print("Delays were capped at 2 seconds (instead of 1s, 2s, 4s, 8s)")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("RetryManager Usage Examples")
    print("=" * 60)
    
    # Run async examples
    await example_basic_async_retry()
    await example_decorator()
    await example_custom_strategy()
    await example_with_error_handler()
    await example_price_api_with_retry()
    await example_max_delay_cap()
    
    # Run sync example
    example_sync_retry()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
