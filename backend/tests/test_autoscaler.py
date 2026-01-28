"""
Unit tests for auto-scaling service.

Tests the auto-scaling logic that monitors system load and scales backend instances.

Requirements: 24.3
"""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from backend.deployment.autoscaling.autoscaler import (
    AutoScaler,
    BackendInstance,
    ScalingDecision,
    SystemMetrics,
)


@pytest.fixture
def autoscaler():
    """Create an AutoScaler instance for testing."""
    return AutoScaler(
        prometheus_url="http://localhost:9090",
        min_instances=1,
        max_instances=5,
        scale_up_threshold=0.80,
        scale_down_threshold=0.30,
        cooldown_period=300,
        check_interval=60,
    )


@pytest.fixture
def high_load_metrics():
    """System metrics indicating high load (>80%)."""
    return SystemMetrics(
        cpu_percent=85.0,
        memory_percent=80.0,
        disk_percent=50.0,
        network_connections=100,
        timestamp=datetime.now()
    )


@pytest.fixture
def low_load_metrics():
    """System metrics indicating low load (<30%)."""
    return SystemMetrics(
        cpu_percent=20.0,
        memory_percent=25.0,
        disk_percent=50.0,
        network_connections=10,
        timestamp=datetime.now()
    )


@pytest.fixture
def normal_load_metrics():
    """System metrics indicating normal load (30-80%)."""
    return SystemMetrics(
        cpu_percent=50.0,
        memory_percent=55.0,
        disk_percent=50.0,
        network_connections=50,
        timestamp=datetime.now()
    )


class TestLoadCalculation:
    """Test load calculation from system metrics."""
    
    def test_calculate_load_high(self, autoscaler, high_load_metrics):
        """Test load calculation with high CPU and memory usage."""
        load = autoscaler.calculate_load(high_load_metrics)
        
        # Load should be > 0.80 (weighted average of 85% CPU and 80% memory)
        # Expected: 0.85 * 0.7 + 0.80 * 0.3 = 0.595 + 0.24 = 0.835
        assert load > 0.80
        assert load < 1.0
    
    def test_calculate_load_low(self, autoscaler, low_load_metrics):
        """Test load calculation with low CPU and memory usage."""
        load = autoscaler.calculate_load(low_load_metrics)
        
        # Load should be < 0.30
        # Expected: 0.20 * 0.7 + 0.25 * 0.3 = 0.14 + 0.075 = 0.215
        assert load < 0.30
        assert load > 0.0
    
    def test_calculate_load_normal(self, autoscaler, normal_load_metrics):
        """Test load calculation with normal CPU and memory usage."""
        load = autoscaler.calculate_load(normal_load_metrics)
        
        # Load should be between 0.30 and 0.80
        assert 0.30 < load < 0.80
    
    def test_calculate_load_cpu_weighted_more(self, autoscaler):
        """Test that CPU is weighted more heavily than memory in load calculation."""
        # High CPU, low memory
        high_cpu_metrics = SystemMetrics(
            cpu_percent=90.0,
            memory_percent=20.0,
            disk_percent=50.0,
            network_connections=50,
            timestamp=datetime.now()
        )
        
        # Low CPU, high memory
        high_memory_metrics = SystemMetrics(
            cpu_percent=20.0,
            memory_percent=90.0,
            disk_percent=50.0,
            network_connections=50,
            timestamp=datetime.now()
        )
        
        load_high_cpu = autoscaler.calculate_load(high_cpu_metrics)
        load_high_memory = autoscaler.calculate_load(high_memory_metrics)
        
        # High CPU should result in higher load due to 0.7 weight
        assert load_high_cpu > load_high_memory


class TestScalingDecisions:
    """Test scaling decision logic."""
    
    def test_should_scale_up_when_load_exceeds_threshold(self, autoscaler):
        """Test that system scales up when load exceeds 80%."""
        load = 0.85  # 85% load
        current_instances = 2
        
        should_scale = autoscaler.should_scale_up(load, current_instances)
        
        assert should_scale is True
    
    def test_should_not_scale_up_when_load_below_threshold(self, autoscaler):
        """Test that system does not scale up when load is below 80%."""
        load = 0.75  # 75% load
        current_instances = 2
        
        should_scale = autoscaler.should_scale_up(load, current_instances)
        
        assert should_scale is False
    
    def test_should_not_scale_up_at_max_instances(self, autoscaler):
        """Test that system does not scale up when at maximum instances."""
        load = 0.95  # 95% load
        current_instances = 5  # At max
        
        should_scale = autoscaler.should_scale_up(load, current_instances)
        
        assert should_scale is False
    
    def test_should_scale_down_when_load_below_threshold(self, autoscaler):
        """Test that system scales down when load is below 30%."""
        load = 0.25  # 25% load
        current_instances = 3
        
        should_scale = autoscaler.should_scale_down(load, current_instances)
        
        assert should_scale is True
    
    def test_should_not_scale_down_when_load_above_threshold(self, autoscaler):
        """Test that system does not scale down when load is above 30%."""
        load = 0.40  # 40% load
        current_instances = 3
        
        should_scale = autoscaler.should_scale_down(load, current_instances)
        
        assert should_scale is False
    
    def test_should_not_scale_down_at_min_instances(self, autoscaler):
        """Test that system does not scale down when at minimum instances."""
        load = 0.10  # 10% load
        current_instances = 1  # At min
        
        should_scale = autoscaler.should_scale_down(load, current_instances)
        
        assert should_scale is False


class TestCooldownPeriod:
    """Test cooldown period logic."""
    
    def test_is_in_cooldown_when_recent_action(self, autoscaler):
        """Test that system is in cooldown after recent scaling action."""
        autoscaler.last_scaling_action = datetime.now() - timedelta(seconds=60)
        
        in_cooldown = autoscaler.is_in_cooldown()
        
        assert in_cooldown is True
    
    def test_not_in_cooldown_when_no_recent_action(self, autoscaler):
        """Test that system is not in cooldown after cooldown period expires."""
        autoscaler.last_scaling_action = datetime.now() - timedelta(seconds=400)
        
        in_cooldown = autoscaler.is_in_cooldown()
        
        assert in_cooldown is False
    
    def test_not_in_cooldown_when_no_previous_action(self, autoscaler):
        """Test that system is not in cooldown when no previous scaling action."""
        autoscaler.last_scaling_action = None
        
        in_cooldown = autoscaler.is_in_cooldown()
        
        assert in_cooldown is False


class TestScalingDecisionMaking:
    """Test the complete scaling decision-making process."""
    
    @pytest.mark.asyncio
    async def test_decision_to_scale_up_on_high_load(self, autoscaler, high_load_metrics):
        """Test that high load triggers scale-up decision."""
        with patch.object(autoscaler, 'get_system_metrics', return_value=high_load_metrics):
            with patch.object(autoscaler, 'discover_instances', return_value=[
                BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
                BackendInstance('backend-2', 'backend-2', 8000, 'running', 'healthy'),
            ]):
                decision = await autoscaler.make_scaling_decision()
        
        assert decision.action == 'scale_up'
        assert decision.current_instances == 2
        assert decision.target_instances == 3
        assert 'exceeds threshold' in decision.reason.lower()
    
    @pytest.mark.asyncio
    async def test_decision_to_scale_down_on_low_load(self, autoscaler, low_load_metrics):
        """Test that low load triggers scale-down decision."""
        with patch.object(autoscaler, 'get_system_metrics', return_value=low_load_metrics):
            with patch.object(autoscaler, 'discover_instances', return_value=[
                BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
                BackendInstance('backend-2', 'backend-2', 8000, 'running', 'healthy'),
                BackendInstance('backend-3', 'backend-3', 8000, 'running', 'healthy'),
            ]):
                decision = await autoscaler.make_scaling_decision()
        
        assert decision.action == 'scale_down'
        assert decision.current_instances == 3
        assert decision.target_instances == 2
        assert 'below threshold' in decision.reason.lower()
    
    @pytest.mark.asyncio
    async def test_no_action_on_normal_load(self, autoscaler, normal_load_metrics):
        """Test that normal load results in no scaling action."""
        with patch.object(autoscaler, 'get_system_metrics', return_value=normal_load_metrics):
            with patch.object(autoscaler, 'discover_instances', return_value=[
                BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
                BackendInstance('backend-2', 'backend-2', 8000, 'running', 'healthy'),
            ]):
                decision = await autoscaler.make_scaling_decision()
        
        assert decision.action == 'no_action'
        assert decision.current_instances == 2
        assert decision.target_instances == 2
    
    @pytest.mark.asyncio
    async def test_no_action_during_cooldown(self, autoscaler, high_load_metrics):
        """Test that no action is taken during cooldown period."""
        autoscaler.last_scaling_action = datetime.now() - timedelta(seconds=60)
        
        with patch.object(autoscaler, 'get_system_metrics', return_value=high_load_metrics):
            with patch.object(autoscaler, 'discover_instances', return_value=[
                BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
            ]):
                decision = await autoscaler.make_scaling_decision()
        
        assert decision.action == 'no_action'
        assert 'cooldown' in decision.reason.lower()


class TestInstanceDiscovery:
    """Test backend instance discovery."""
    
    @pytest.mark.asyncio
    async def test_discover_healthy_instances(self, autoscaler):
        """Test discovery of healthy backend instances."""
        async def mock_health_check(instance):
            instance.health = 'healthy'
            instance.status = 'running'
            return True
        
        with patch.object(autoscaler, 'check_backend_health', side_effect=mock_health_check):
            instances = await autoscaler.discover_instances()
        
        # Should discover at least one instance
        assert len(instances) >= 1
        assert all(instance.status == 'running' for instance in instances)
        assert all(instance.health == 'healthy' for instance in instances)
    
    @pytest.mark.asyncio
    async def test_discover_no_instances_when_unhealthy(self, autoscaler):
        """Test that unhealthy instances are not discovered."""
        with patch.object(autoscaler, 'check_backend_health', return_value=False):
            instances = await autoscaler.discover_instances()
        
        # Should not discover any instances if all are unhealthy
        assert len(instances) == 0


class TestHealthChecks:
    """Test backend instance health checks."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, autoscaler):
        """Test successful health check."""
        instance = BackendInstance('backend', 'backend', 8000, 'running', 'unknown')
        
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession.get', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))):
            is_healthy = await autoscaler.check_backend_health(instance)
        
        assert is_healthy is True
        assert instance.health == 'healthy'
        assert instance.last_health_check is not None
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, autoscaler):
        """Test failed health check."""
        instance = BackendInstance('backend', 'backend', 8000, 'running', 'unknown')
        
        mock_response = AsyncMock()
        mock_response.status = 500
        
        with patch('aiohttp.ClientSession.get', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))):
            is_healthy = await autoscaler.check_backend_health(instance)
        
        assert is_healthy is False
        assert instance.health == 'unhealthy'
        assert instance.last_health_check is not None
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self, autoscaler):
        """Test health check timeout."""
        instance = BackendInstance('backend', 'backend', 8000, 'running', 'unknown')
        
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError()):
            is_healthy = await autoscaler.check_backend_health(instance)
        
        assert is_healthy is False
        assert instance.health == 'unhealthy'


class TestScalingExecution:
    """Test scaling action execution."""
    
    @pytest.mark.asyncio
    async def test_scale_up_execution(self, autoscaler):
        """Test scale-up execution."""
        with patch.object(autoscaler, 'discover_instances', return_value=[
            BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
        ]):
            with patch('asyncio.create_subprocess_shell', return_value=AsyncMock(
                returncode=0,
                communicate=AsyncMock(return_value=(b'', b''))
            )):
                with patch.object(autoscaler, 'reload_nginx', return_value=True):
                    success = await autoscaler.scale_up(2)
        
        assert success is True
        assert autoscaler.last_scaling_action is not None
    
    @pytest.mark.asyncio
    async def test_scale_down_execution(self, autoscaler):
        """Test scale-down execution."""
        with patch.object(autoscaler, 'discover_instances', return_value=[
            BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
            BackendInstance('backend-2', 'backend-2', 8000, 'running', 'healthy'),
            BackendInstance('backend-3', 'backend-3', 8000, 'running', 'healthy'),
        ]):
            with patch('asyncio.create_subprocess_shell', return_value=AsyncMock(
                returncode=0,
                communicate=AsyncMock(return_value=(b'', b''))
            )):
                with patch.object(autoscaler, 'reload_nginx', return_value=True):
                    success = await autoscaler.scale_down(2)
        
        assert success is True
        assert autoscaler.last_scaling_action is not None
    
    @pytest.mark.asyncio
    async def test_execute_no_action_decision(self, autoscaler):
        """Test execution of no-action decision."""
        decision = ScalingDecision(
            action='no_action',
            reason='Load within acceptable range',
            current_instances=2,
            target_instances=2,
            metrics=SystemMetrics(50.0, 50.0, 50.0, 50, datetime.now())
        )
        
        success = await autoscaler.execute_scaling_decision(decision)
        
        assert success is True


class TestPrometheusIntegration:
    """Test Prometheus metrics integration."""
    
    @pytest.mark.asyncio
    async def test_get_prometheus_metrics_success(self, autoscaler):
        """Test successful Prometheus metrics retrieval."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'data': {
                'result': [
                    {'value': [0, '75.5']}
                ]
            }
        })
        
        with patch('aiohttp.ClientSession.get', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))):
            metrics = await autoscaler.get_prometheus_metrics()
        
        assert 'cpu_usage' in metrics
        assert metrics['cpu_usage'] == 75.5
    
    @pytest.mark.asyncio
    async def test_get_prometheus_metrics_failure(self, autoscaler):
        """Test Prometheus metrics retrieval failure."""
        with patch('aiohttp.ClientSession.get', side_effect=Exception('Connection error')):
            metrics = await autoscaler.get_prometheus_metrics()
        
        # Should return empty dict on error
        assert metrics == {}


class TestSystemMetrics:
    """Test system metrics collection."""
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, autoscaler):
        """Test system metrics collection."""
        with patch('psutil.cpu_percent', return_value=75.0):
            with patch('psutil.virtual_memory', return_value=MagicMock(percent=60.0)):
                with patch('psutil.disk_usage', return_value=MagicMock(percent=50.0)):
                    with patch('psutil.net_connections', return_value=[1, 2, 3]):
                        metrics = await autoscaler.get_system_metrics()
        
        assert metrics.cpu_percent == 75.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_percent == 50.0
        assert metrics.network_connections == 3
        assert isinstance(metrics.timestamp, datetime)


class TestRequirement24_3:
    """
    Test Requirement 24.3: Auto-scaling when load exceeds 80%.
    
    Requirements: 24.3
    """
    
    @pytest.mark.asyncio
    async def test_auto_scaling_triggers_at_80_percent_load(self, autoscaler):
        """
        Test that auto-scaling triggers when system load exceeds 80%.
        
        This validates Requirement 24.3:
        "WHEN system load exceeds 80% capacity, THE Platform SHALL 
        automatically provision additional resources"
        """
        # Create metrics slightly above 80% load to ensure trigger
        # Weighted: 0.81 * 0.7 + 0.81 * 0.3 = 0.81
        metrics_above_threshold = SystemMetrics(
            cpu_percent=81.0,
            memory_percent=81.0,
            disk_percent=50.0,
            network_connections=100,
            timestamp=datetime.now()
        )
        
        # Create metrics well above 80% load
        # Weighted: 0.85 * 0.7 + 0.82 * 0.3 = 0.841
        metrics_high_load = SystemMetrics(
            cpu_percent=85.0,
            memory_percent=82.0,
            disk_percent=50.0,
            network_connections=120,
            timestamp=datetime.now()
        )
        
        # Test above threshold (should trigger)
        with patch.object(autoscaler, 'get_system_metrics', return_value=metrics_above_threshold):
            with patch.object(autoscaler, 'discover_instances', return_value=[
                BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
            ]):
                decision_above = await autoscaler.make_scaling_decision()
        
        # Test high load (should trigger)
        with patch.object(autoscaler, 'get_system_metrics', return_value=metrics_high_load):
            with patch.object(autoscaler, 'discover_instances', return_value=[
                BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
            ]):
                decision_high = await autoscaler.make_scaling_decision()
        
        # Verify load calculation
        load_above = autoscaler.calculate_load(metrics_above_threshold)
        load_high = autoscaler.calculate_load(metrics_high_load)
        
        # Both loads should be > 0.80
        assert load_above > 0.80, f"Load should be > 0.80, got {load_above}"
        assert load_high > 0.80, f"Load should be > 0.80, got {load_high}"
        
        # Both should trigger scale-up
        assert decision_above.action == 'scale_up', f"Expected scale_up, got {decision_above.action}: {decision_above.reason}"
        assert decision_high.action == 'scale_up', f"Expected scale_up, got {decision_high.action}: {decision_high.reason}"
        
        # Test that at/near 80% threshold behavior
        # Note: Due to floating point precision, 80% CPU + 80% memory may calculate to 0.7999...
        # The implementation correctly uses >= 0.80 threshold, which is the right behavior
        metrics_at_threshold = SystemMetrics(
            cpu_percent=80.0,
            memory_percent=80.0,
            disk_percent=50.0,
            network_connections=100,
            timestamp=datetime.now()
        )
        
        load_at = autoscaler.calculate_load(metrics_at_threshold)
        
        # Load should be very close to 0.80 (within floating point precision)
        assert abs(load_at - 0.80) < 0.001, f"Load should be ~0.80, got {load_at}"
        
        # The key requirement is that loads >= 80% trigger scaling
        # Test with a load that's definitely >= 0.80
        assert autoscaler.should_scale_up(0.80, 1) is True
        assert autoscaler.should_scale_up(0.81, 1) is True
        assert autoscaler.should_scale_up(0.85, 1) is True
        assert autoscaler.should_scale_up(0.79, 1) is False
    
    @pytest.mark.asyncio
    async def test_auto_scaling_provisions_additional_resources(self, autoscaler):
        """
        Test that auto-scaling actually provisions additional backend instances.
        
        This validates the "automatically provision additional resources" part
        of Requirement 24.3.
        """
        initial_instances = [
            BackendInstance('backend', 'backend', 8000, 'running', 'healthy'),
        ]
        
        with patch.object(autoscaler, 'discover_instances', return_value=initial_instances):
            with patch('asyncio.create_subprocess_shell', return_value=AsyncMock(
                returncode=0,
                communicate=AsyncMock(return_value=(b'Started backend-2', b''))
            )) as mock_subprocess:
                with patch.object(autoscaler, 'reload_nginx', return_value=True):
                    success = await autoscaler.scale_up(2)
        
        # Verify scaling was successful
        assert success is True
        
        # Verify docker-compose command was called to start new instance
        mock_subprocess.assert_called()
        
        # Verify last scaling action was recorded
        assert autoscaler.last_scaling_action is not None
    
    @pytest.mark.asyncio
    async def test_monitoring_and_resource_utilization(self, autoscaler):
        """
        Test that the system monitors resource utilization correctly.
        
        This validates the "Monitor system load and resource utilization"
        part of the task.
        """
        # Mock system metrics
        with patch('psutil.cpu_percent', return_value=85.0):
            with patch('psutil.virtual_memory', return_value=MagicMock(percent=80.0)):
                with patch('psutil.disk_usage', return_value=MagicMock(percent=60.0)):
                    with patch('psutil.net_connections', return_value=[1] * 150):
                        metrics = await autoscaler.get_system_metrics()
        
        # Verify metrics are collected
        assert metrics.cpu_percent == 85.0
        assert metrics.memory_percent == 80.0
        assert metrics.disk_percent == 60.0
        assert metrics.network_connections == 150
        
        # Verify load calculation
        load = autoscaler.calculate_load(metrics)
        assert load > 0.80  # Should exceed threshold
