"""Graceful degradation manager for handling critical service failures

This service provides:
- Service health tracking
- Fallback strategies for critical services
- Degraded mode operation
- Available functionality when services are down

Requirements: 14.5
"""
import logging
from typing import Dict, Optional, Any, Callable, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Types of services in the system"""
    STT = "stt"  # Speech-to-Text
    TRANSLATION = "translation"
    TTS = "tts"  # Text-to-Speech
    LLM = "llm"  # Language Model for negotiation
    PRICE_ORACLE = "price_oracle"
    VOICE_BIOMETRIC = "voice_biometric"
    DATABASE = "database"
    CACHE = "cache"


class ServiceStatus(str, Enum):
    """Status of a service"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class ServiceHealth:
    """Health information for a service"""
    service_type: ServiceType
    status: ServiceStatus
    last_check: datetime
    failure_count: int = 0
    last_error: Optional[str] = None
    fallback_available: bool = False
    fallback_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "service_type": self.service_type.value,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "fallback_available": self.fallback_available,
            "fallback_description": self.fallback_description,
        }


@dataclass
class DegradedModeConfig:
    """Configuration for degraded mode operation"""
    # Maximum failures before marking service as unavailable
    max_failures: int = 3
    
    # Time window for failure counting (seconds)
    failure_window: int = 300  # 5 minutes
    
    # Time to wait before retrying unavailable service (seconds)
    retry_interval: int = 60  # 1 minute
    
    # Whether to automatically enable fallbacks
    auto_fallback: bool = True
    
    # Services that are critical (system cannot function without them)
    critical_services: List[ServiceType] = field(default_factory=lambda: [
        ServiceType.DATABASE,
    ])
    
    # Services that have fallbacks
    services_with_fallbacks: Dict[ServiceType, str] = field(default_factory=lambda: {
        ServiceType.STT: "Use cached transcriptions or text input",
        ServiceType.TRANSLATION: "Use cached translations or show original text",
        ServiceType.TTS: "Show text output instead of audio",
        ServiceType.LLM: "Use template-based suggestions",
        ServiceType.PRICE_ORACLE: "Use cached price data or demo data",
        ServiceType.VOICE_BIOMETRIC: "Use PIN-based authentication",
        ServiceType.CACHE: "Use in-memory cache or direct database access",
    })


class GracefulDegradationManager:
    """Manages graceful degradation when services fail"""
    
    def __init__(self, config: Optional[DegradedModeConfig] = None):
        """
        Initialize graceful degradation manager
        
        Args:
            config: Configuration for degraded mode operation
        """
        self.config = config or DegradedModeConfig()
        self.service_health: Dict[ServiceType, ServiceHealth] = {}
        self._initialize_services()
        self._fallback_handlers: Dict[ServiceType, Callable] = {}
        self._lock = asyncio.Lock()
    
    def _initialize_services(self):
        """Initialize service health tracking"""
        for service_type in ServiceType:
            self.service_health[service_type] = ServiceHealth(
                service_type=service_type,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                fallback_available=service_type in self.config.services_with_fallbacks,
                fallback_description=self.config.services_with_fallbacks.get(service_type)
            )
    
    def register_fallback_handler(
        self,
        service_type: ServiceType,
        handler: Callable
    ):
        """
        Register a fallback handler for a service
        
        Args:
            service_type: Type of service
            handler: Callable that provides fallback functionality
        """
        self._fallback_handlers[service_type] = handler
        logger.info(f"Registered fallback handler for {service_type.value}")
    
    async def record_service_failure(
        self,
        service_type: ServiceType,
        error: Exception
    ):
        """
        Record a service failure and update health status
        
        Args:
            service_type: Type of service that failed
            error: The exception that occurred
        """
        async with self._lock:
            health = self.service_health[service_type]
            health.failure_count += 1
            health.last_error = str(error)
            health.last_check = datetime.now()
            
            # Update status based on failure count
            if health.failure_count >= self.config.max_failures:
                health.status = ServiceStatus.UNAVAILABLE
                logger.error(
                    f"Service {service_type.value} marked as UNAVAILABLE after "
                    f"{health.failure_count} failures"
                )
            elif health.failure_count > 0:
                health.status = ServiceStatus.DEGRADED
                logger.warning(
                    f"Service {service_type.value} marked as DEGRADED "
                    f"({health.failure_count} failures)"
                )
            
            # Check if this is a critical service
            if service_type in self.config.critical_services:
                logger.critical(
                    f"Critical service {service_type.value} is {health.status.value}!"
                )
    
    async def record_service_success(
        self,
        service_type: ServiceType
    ):
        """
        Record a successful service call and update health status
        
        Args:
            service_type: Type of service that succeeded
        """
        async with self._lock:
            health = self.service_health[service_type]
            
            # Reset failure count on success
            if health.failure_count > 0:
                logger.info(
                    f"Service {service_type.value} recovered after "
                    f"{health.failure_count} failures"
                )
            
            health.failure_count = 0
            health.status = ServiceStatus.HEALTHY
            health.last_error = None
            health.last_check = datetime.now()
    
    def get_service_status(
        self,
        service_type: ServiceType
    ) -> ServiceStatus:
        """
        Get current status of a service
        
        Args:
            service_type: Type of service
            
        Returns:
            Current service status
        """
        return self.service_health[service_type].status
    
    def is_service_available(
        self,
        service_type: ServiceType
    ) -> bool:
        """
        Check if a service is available (healthy or degraded)
        
        Args:
            service_type: Type of service
            
        Returns:
            True if service is available, False otherwise
        """
        status = self.get_service_status(service_type)
        return status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
    
    def has_fallback(
        self,
        service_type: ServiceType
    ) -> bool:
        """
        Check if a service has a fallback available
        
        Args:
            service_type: Type of service
            
        Returns:
            True if fallback is available, False otherwise
        """
        return self.service_health[service_type].fallback_available
    
    async def execute_with_fallback(
        self,
        service_type: ServiceType,
        primary_operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation with automatic fallback on failure
        
        Args:
            service_type: Type of service being called
            primary_operation: Primary operation to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result from primary operation or fallback
            
        Raises:
            Exception if both primary and fallback fail
        """
        # Check if service is unavailable
        if not self.is_service_available(service_type):
            logger.warning(
                f"Service {service_type.value} is unavailable, using fallback"
            )
            return await self._execute_fallback(service_type, *args, **kwargs)
        
        try:
            # Try primary operation
            result = await primary_operation(*args, **kwargs)
            
            # Record success
            await self.record_service_success(service_type)
            
            return result
            
        except Exception as e:
            # Record failure
            await self.record_service_failure(service_type, e)
            
            # Try fallback if available and auto-fallback is enabled
            if self.config.auto_fallback and self.has_fallback(service_type):
                logger.warning(
                    f"Primary operation failed for {service_type.value}, "
                    f"attempting fallback. Error: {type(e).__name__}"
                )
                try:
                    return await self._execute_fallback(service_type, *args, **kwargs)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback also failed for {service_type.value}: "
                        f"{type(fallback_error).__name__}"
                    )
                    raise
            else:
                # No fallback available or auto-fallback disabled
                raise
    
    async def _execute_fallback(
        self,
        service_type: ServiceType,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute fallback handler for a service
        
        Args:
            service_type: Type of service
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from fallback handler
            
        Raises:
            ValueError if no fallback handler is registered
        """
        if service_type not in self._fallback_handlers:
            raise ValueError(
                f"No fallback handler registered for {service_type.value}"
            )
        
        handler = self._fallback_handlers[service_type]
        
        # Execute fallback handler
        if asyncio.iscoroutinefunction(handler):
            return await handler(*args, **kwargs)
        else:
            return handler(*args, **kwargs)
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health status
        
        Returns:
            Dictionary with system health information
        """
        services = {
            service_type.value: health.to_dict()
            for service_type, health in self.service_health.items()
        }
        
        # Count services by status
        healthy_count = sum(
            1 for h in self.service_health.values()
            if h.status == ServiceStatus.HEALTHY
        )
        degraded_count = sum(
            1 for h in self.service_health.values()
            if h.status == ServiceStatus.DEGRADED
        )
        unavailable_count = sum(
            1 for h in self.service_health.values()
            if h.status == ServiceStatus.UNAVAILABLE
        )
        
        # Determine overall system status
        if unavailable_count > 0:
            # Check if any critical services are unavailable
            critical_unavailable = any(
                self.service_health[s].status == ServiceStatus.UNAVAILABLE
                for s in self.config.critical_services
            )
            if critical_unavailable:
                overall_status = "critical"
            else:
                overall_status = "degraded"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "healthy_services": healthy_count,
            "degraded_services": degraded_count,
            "unavailable_services": unavailable_count,
            "total_services": len(self.service_health),
            "services": services,
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_available_features(self) -> Dict[str, bool]:
        """
        Get list of features and their availability
        
        Returns:
            Dictionary mapping feature names to availability status
        """
        return {
            "voice_input": self.is_service_available(ServiceType.STT),
            "voice_output": self.is_service_available(ServiceType.TTS),
            "translation": self.is_service_available(ServiceType.TRANSLATION),
            "price_check": self.is_service_available(ServiceType.PRICE_ORACLE),
            "negotiation_assistance": self.is_service_available(ServiceType.LLM),
            "voice_authentication": self.is_service_available(ServiceType.VOICE_BIOMETRIC),
            "data_persistence": self.is_service_available(ServiceType.DATABASE),
            "caching": self.is_service_available(ServiceType.CACHE),
        }
    
    async def reset_service_health(
        self,
        service_type: ServiceType
    ):
        """
        Manually reset service health (for testing or manual recovery)
        
        Args:
            service_type: Type of service to reset
        """
        async with self._lock:
            self.service_health[service_type] = ServiceHealth(
                service_type=service_type,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                fallback_available=service_type in self.config.services_with_fallbacks,
                fallback_description=self.config.services_with_fallbacks.get(service_type)
            )
            logger.info(f"Reset health for service {service_type.value}")


# Global instance for easy access
_degradation_manager: Optional[GracefulDegradationManager] = None


def get_degradation_manager() -> GracefulDegradationManager:
    """
    Get the global graceful degradation manager instance
    
    Returns:
        GracefulDegradationManager instance
    """
    global _degradation_manager
    if _degradation_manager is None:
        _degradation_manager = GracefulDegradationManager()
    return _degradation_manager


def set_degradation_manager(manager: GracefulDegradationManager):
    """
    Set the global graceful degradation manager instance
    
    Args:
        manager: GracefulDegradationManager instance to use
    """
    global _degradation_manager
    _degradation_manager = manager
