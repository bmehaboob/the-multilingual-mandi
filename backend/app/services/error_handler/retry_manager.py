"""Retry manager with exponential backoff

This service provides:
- Retry logic for failed service calls (max 3 retries)
- Exponential backoff (1s, 2s, 4s)
- Configurable retry strategies

Requirements: 14.3
"""
import asyncio
import logging
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryManager:
    """Manages retry logic for failed operations with exponential backoff"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: Optional[float] = None
    ):
        """
        Initialize retry manager
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
            max_delay: Maximum delay in seconds (optional cap on exponential growth)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def retry_with_backoff(
        self,
        operation: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Retries an async operation with exponential backoff
        
        Delays: 1s, 2s, 4s (for default base_delay=1.0)
        
        Args:
            operation: Async callable to retry
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation if successful
            
        Raises:
            The last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Attempt the operation
                result = await operation(*args, **kwargs)
                
                # Log success if this was a retry
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1}/{self.max_retries}"
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Operation failed after {self.max_retries} attempts: {type(e).__name__}"
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                
                # Apply max_delay cap if specified
                if self.max_delay is not None:
                    delay = min(delay, self.max_delay)
                
                logger.warning(
                    f"Operation failed on attempt {attempt + 1}/{self.max_retries}. "
                    f"Retrying in {delay}s... Error: {type(e).__name__}"
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    def retry_sync_with_backoff(
        self,
        operation: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        Retries a synchronous operation with exponential backoff
        
        Delays: 1s, 2s, 4s (for default base_delay=1.0)
        
        Args:
            operation: Synchronous callable to retry
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation if successful
            
        Raises:
            The last exception if all retries fail
        """
        import time
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Attempt the operation
                result = operation(*args, **kwargs)
                
                # Log success if this was a retry
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1}/{self.max_retries}"
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Operation failed after {self.max_retries} attempts: {type(e).__name__}"
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                
                # Apply max_delay cap if specified
                if self.max_delay is not None:
                    delay = min(delay, self.max_delay)
                
                logger.warning(
                    f"Operation failed on attempt {attempt + 1}/{self.max_retries}. "
                    f"Retrying in {delay}s... Error: {type(e).__name__}"
                )
                
                # Wait before retrying
                time.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    async def retry_with_custom_strategy(
        self,
        operation: Callable[..., Any],
        retry_on: Optional[List[type]] = None,
        max_retries: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Retries an async operation with custom retry strategy
        
        Args:
            operation: Async callable to retry
            retry_on: List of exception types to retry on (None = retry on all)
            max_retries: Override default max_retries for this operation
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation if successful
            
        Raises:
            The last exception if all retries fail or if exception not in retry_on list
        """
        retries = max_retries if max_retries is not None else self.max_retries
        last_exception = None
        
        for attempt in range(retries):
            try:
                result = await operation(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1}/{retries}"
                    )
                
                return result
                
            except Exception as e:
                # Check if we should retry this exception type
                if retry_on is not None and not isinstance(e, tuple(retry_on)):
                    logger.info(
                        f"Exception {type(e).__name__} not in retry list. Not retrying."
                    )
                    raise
                
                last_exception = e
                
                if attempt == retries - 1:
                    logger.error(
                        f"Operation failed after {retries} attempts: {type(e).__name__}"
                    )
                    raise
                
                delay = self.base_delay * (2 ** attempt)
                if self.max_delay is not None:
                    delay = min(delay, self.max_delay)
                
                logger.warning(
                    f"Operation failed on attempt {attempt + 1}/{retries}. "
                    f"Retrying in {delay}s... Error: {type(e).__name__}"
                )
                
                await asyncio.sleep(delay)
        
        if last_exception:
            raise last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: Optional[float] = None
):
    """
    Decorator for adding retry logic to async functions
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
        
    Example:
        @with_retry(max_retries=3, base_delay=1.0)
        async def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_manager = RetryManager(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            return await retry_manager.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator


def with_retry_sync(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: Optional[float] = None
):
    """
    Decorator for adding retry logic to synchronous functions
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
        
    Example:
        @with_retry_sync(max_retries=3, base_delay=1.0)
        def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = RetryManager(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            return retry_manager.retry_sync_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator
