"""Example usage of the Graceful Degradation Manager

This example demonstrates:
1. Setting up the degradation manager
2. Registering fallback handlers
3. Executing operations with automatic fallback
4. Monitoring system health
5. Handling service failures gracefully

Requirements: 14.5
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.error_handler import (
    GracefulDegradationManager,
    ServiceType,
    ServiceStatus,
    DegradedModeConfig,
)


# Example: STT Service with fallback
class STTService:
    """Example Speech-to-Text service"""
    
    def __init__(self, degradation_manager: GracefulDegradationManager):
        self.manager = degradation_manager
        self.is_working = True  # Simulate service health
        
        # Register fallback handler
        self.manager.register_fallback_handler(
            ServiceType.STT,
            self.fallback_transcribe
        )
    
    async def transcribe(self, audio_data: bytes) -> str:
        """Primary transcription method"""
        if not self.is_working:
            raise Exception("STT service is down")
        
        # Simulate transcription
        return f"Transcribed: {len(audio_data)} bytes"
    
    async def fallback_transcribe(self, audio_data: bytes) -> str:
        """Fallback: Use cached transcriptions or prompt for text input"""
        print("⚠️  STT service unavailable, using fallback")
        return f"[FALLBACK] Please type your message (audio was {len(audio_data)} bytes)"
    
    async def transcribe_with_degradation(self, audio_data: bytes) -> str:
        """Transcribe with automatic fallback"""
        return await self.manager.execute_with_fallback(
            ServiceType.STT,
            self.transcribe,
            audio_data
        )


# Example: Price Oracle with fallback
class PriceOracleService:
    """Example Price Oracle service"""
    
    def __init__(self, degradation_manager: GracefulDegradationManager):
        self.manager = degradation_manager
        self.api_available = True
        
        # Register fallback handler
        self.manager.register_fallback_handler(
            ServiceType.PRICE_ORACLE,
            self.fallback_get_price
        )
    
    async def get_price(self, commodity: str) -> float:
        """Primary price fetching method"""
        if not self.api_available:
            raise Exception("Price API is down")
        
        # Simulate API call
        return 100.0
    
    async def fallback_get_price(self, commodity: str) -> float:
        """Fallback: Use cached or demo data"""
        print(f"⚠️  Price API unavailable, using cached data for {commodity}")
        # Return cached/demo price
        return 95.0  # Cached price
    
    async def get_price_with_degradation(self, commodity: str) -> float:
        """Get price with automatic fallback"""
        return await self.manager.execute_with_fallback(
            ServiceType.PRICE_ORACLE,
            self.get_price,
            commodity
        )


async def example_basic_usage():
    """Example 1: Basic usage with automatic fallback"""
    print("\n" + "="*60)
    print("Example 1: Basic Usage with Automatic Fallback")
    print("="*60)
    
    # Create manager
    manager = GracefulDegradationManager()
    
    # Create services
    stt_service = STTService(manager)
    
    # Test 1: Service working normally
    print("\n1. Service working normally:")
    audio = b"sample audio data"
    result = await stt_service.transcribe_with_degradation(audio)
    print(f"   Result: {result}")
    print(f"   Service status: {manager.get_service_status(ServiceType.STT)}")
    
    # Test 2: Service fails, fallback is used
    print("\n2. Service fails, fallback is used:")
    stt_service.is_working = False
    result = await stt_service.transcribe_with_degradation(audio)
    print(f"   Result: {result}")
    print(f"   Service status: {manager.get_service_status(ServiceType.STT)}")


async def example_service_recovery():
    """Example 2: Service failure and recovery"""
    print("\n" + "="*60)
    print("Example 2: Service Failure and Recovery")
    print("="*60)
    
    manager = GracefulDegradationManager()
    price_service = PriceOracleService(manager)
    
    # Test 1: Normal operation
    print("\n1. Normal operation:")
    price = await price_service.get_price_with_degradation("tomato")
    print(f"   Price: ₹{price}")
    print(f"   Service status: {manager.get_service_status(ServiceType.PRICE_ORACLE)}")
    
    # Test 2: Service fails multiple times
    print("\n2. Service fails (attempt 1):")
    price_service.api_available = False
    price = await price_service.get_price_with_degradation("tomato")
    print(f"   Price: ₹{price} (from fallback)")
    print(f"   Service status: {manager.get_service_status(ServiceType.PRICE_ORACLE)}")
    
    print("\n3. Service fails (attempt 2):")
    price = await price_service.get_price_with_degradation("tomato")
    print(f"   Price: ₹{price} (from fallback)")
    print(f"   Service status: {manager.get_service_status(ServiceType.PRICE_ORACLE)}")
    
    print("\n4. Service fails (attempt 3 - marked unavailable):")
    price = await price_service.get_price_with_degradation("tomato")
    print(f"   Price: ₹{price} (from fallback)")
    print(f"   Service status: {manager.get_service_status(ServiceType.PRICE_ORACLE)}")
    
    # Test 3: Service recovers
    print("\n5. Service recovers:")
    price_service.api_available = True
    price = await price_service.get_price_with_degradation("tomato")
    print(f"   Price: ₹{price}")
    print(f"   Service status: {manager.get_service_status(ServiceType.PRICE_ORACLE)}")


async def example_system_health_monitoring():
    """Example 3: System health monitoring"""
    print("\n" + "="*60)
    print("Example 3: System Health Monitoring")
    print("="*60)
    
    manager = GracefulDegradationManager()
    
    # Simulate some service failures
    await manager.record_service_failure(
        ServiceType.STT,
        Exception("STT model loading failed")
    )
    await manager.record_service_failure(
        ServiceType.TTS,
        Exception("TTS service timeout")
    )
    await manager.record_service_failure(
        ServiceType.TTS,
        Exception("TTS service timeout")
    )
    
    # Get system health
    print("\n1. System Health Report:")
    health = manager.get_system_health()
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   Healthy Services: {health['healthy_services']}")
    print(f"   Degraded Services: {health['degraded_services']}")
    print(f"   Unavailable Services: {health['unavailable_services']}")
    
    # Get available features
    print("\n2. Available Features:")
    features = manager.get_available_features()
    for feature, available in features.items():
        status = "✓ Available" if available else "✗ Unavailable"
        print(f"   {feature}: {status}")
    
    # Get detailed service status
    print("\n3. Detailed Service Status:")
    for service_type in [ServiceType.STT, ServiceType.TTS, ServiceType.TRANSLATION]:
        health = manager.service_health[service_type]
        print(f"   {service_type.value}:")
        print(f"      Status: {health.status.value}")
        print(f"      Failures: {health.failure_count}")
        print(f"      Fallback: {health.fallback_description or 'None'}")


async def example_custom_configuration():
    """Example 4: Custom configuration"""
    print("\n" + "="*60)
    print("Example 4: Custom Configuration")
    print("="*60)
    
    # Create custom configuration
    config = DegradedModeConfig(
        max_failures=2,  # Mark unavailable after 2 failures
        failure_window=60,  # 1 minute window
        retry_interval=30,  # Retry after 30 seconds
        auto_fallback=True,
        critical_services=[ServiceType.DATABASE, ServiceType.CACHE]
    )
    
    manager = GracefulDegradationManager(config)
    
    print(f"\n1. Configuration:")
    print(f"   Max failures: {config.max_failures}")
    print(f"   Failure window: {config.failure_window}s")
    print(f"   Retry interval: {config.retry_interval}s")
    print(f"   Auto fallback: {config.auto_fallback}")
    print(f"   Critical services: {[s.value for s in config.critical_services]}")
    
    # Simulate failures
    print(f"\n2. Simulating failures:")
    for i in range(3):
        await manager.record_service_failure(
            ServiceType.STT,
            Exception(f"Failure {i+1}")
        )
        status = manager.get_service_status(ServiceType.STT)
        print(f"   After failure {i+1}: {status.value}")


async def example_critical_service_failure():
    """Example 5: Critical service failure"""
    print("\n" + "="*60)
    print("Example 5: Critical Service Failure")
    print("="*60)
    
    manager = GracefulDegradationManager()
    
    # Simulate critical service (database) failure
    print("\n1. Simulating database failures:")
    for i in range(3):
        await manager.record_service_failure(
            ServiceType.DATABASE,
            Exception("Database connection lost")
        )
    
    # Check system health
    health = manager.get_system_health()
    print(f"\n2. System Health After Critical Failure:")
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   ⚠️  Critical service (database) is unavailable!")
    
    # Check what features are still available
    print(f"\n3. Available Features:")
    features = manager.get_available_features()
    available_features = [f for f, avail in features.items() if avail]
    unavailable_features = [f for f, avail in features.items() if not avail]
    
    print(f"   Still Available: {', '.join(available_features)}")
    print(f"   Unavailable: {', '.join(unavailable_features)}")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Graceful Degradation Manager - Usage Examples")
    print("="*60)
    
    await example_basic_usage()
    await example_service_recovery()
    await example_system_health_monitoring()
    await example_custom_configuration()
    await example_critical_service_failure()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
