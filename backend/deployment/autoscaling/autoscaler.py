"""
Auto-scaling service for Multilingual Mandi platform.

This service monitors system load and resource utilization, automatically
scaling backend instances when load exceeds defined thresholds.

Requirements: 24.3
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import psutil


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System resource utilization metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_connections: int
    timestamp: datetime


@dataclass
class BackendInstance:
    """Backend instance information."""
    instance_id: str
    host: str
    port: int
    status: str  # 'running', 'stopped', 'starting', 'stopping'
    health: str  # 'healthy', 'unhealthy', 'unknown'
    last_health_check: Optional[datetime] = None


@dataclass
class ScalingDecision:
    """Auto-scaling decision."""
    action: str  # 'scale_up', 'scale_down', 'no_action'
    reason: str
    current_instances: int
    target_instances: int
    metrics: SystemMetrics


class AutoScaler:
    """
    Auto-scaling service that monitors system load and scales backend instances.
    
    Requirements: 24.3
    """
    
    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        nginx_config_path: str = "/etc/nginx/conf.d/multilingual-mandi.conf",
        docker_compose_path: str = "/app/deployment/docker-compose.prod.yml",
        min_instances: int = 1,
        max_instances: int = 10,
        scale_up_threshold: float = 0.80,  # 80% load
        scale_down_threshold: float = 0.30,  # 30% load
        cooldown_period: int = 300,  # 5 minutes in seconds
        check_interval: int = 60,  # 1 minute in seconds
    ):
        """
        Initialize auto-scaler.
        
        Args:
            prometheus_url: Prometheus server URL
            nginx_config_path: Path to Nginx configuration file
            docker_compose_path: Path to Docker Compose file
            min_instances: Minimum number of backend instances
            max_instances: Maximum number of backend instances
            scale_up_threshold: CPU/memory threshold to trigger scale up (0-1)
            scale_down_threshold: CPU/memory threshold to trigger scale down (0-1)
            cooldown_period: Cooldown period between scaling actions (seconds)
            check_interval: Interval between metric checks (seconds)
        """
        self.prometheus_url = prometheus_url
        self.nginx_config_path = nginx_config_path
        self.docker_compose_path = docker_compose_path
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.cooldown_period = cooldown_period
        self.check_interval = check_interval
        
        self.instances: Dict[str, BackendInstance] = {}
        self.last_scaling_action: Optional[datetime] = None
        self.running = False
    
    async def get_system_metrics(self) -> SystemMetrics:
        """
        Get current system resource utilization metrics.
        
        Returns:
            SystemMetrics with current resource usage
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network_connections = len(psutil.net_connections())
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            network_connections=network_connections,
            timestamp=datetime.now()
        )
    
    async def get_prometheus_metrics(self) -> Dict[str, float]:
        """
        Query Prometheus for application-level metrics.
        
        Returns:
            Dictionary of metric names to values
        """
        metrics = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                # Query CPU usage from Prometheus
                cpu_query = 'avg(rate(process_cpu_seconds_total[5m])) * 100'
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': cpu_query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['data']['result']:
                            metrics['cpu_usage'] = float(data['data']['result'][0]['value'][1])
                
                # Query memory usage
                memory_query = 'process_resident_memory_bytes / 1024 / 1024 / 1024'
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': memory_query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['data']['result']:
                            metrics['memory_usage_gb'] = float(data['data']['result'][0]['value'][1])
                
                # Query request rate
                request_query = 'sum(rate(http_requests_total[5m]))'
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': request_query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['data']['result']:
                            metrics['request_rate'] = float(data['data']['result'][0]['value'][1])
                
                # Query active connections
                connections_query = 'sum(active_conversations_total)'
                async with session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={'query': connections_query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['data']['result']:
                            metrics['active_connections'] = float(data['data']['result'][0]['value'][1])
        
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
        
        return metrics
    
    async def check_backend_health(self, instance: BackendInstance) -> bool:
        """
        Check health of a backend instance.
        
        Args:
            instance: Backend instance to check
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{instance.host}:{instance.port}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    is_healthy = response.status == 200
                    instance.health = 'healthy' if is_healthy else 'unhealthy'
                    instance.last_health_check = datetime.now()
                    return is_healthy
        except Exception as e:
            logger.warning(f"Health check failed for {instance.instance_id}: {e}")
            instance.health = 'unhealthy'
            instance.last_health_check = datetime.now()
            return False
    
    async def discover_instances(self) -> List[BackendInstance]:
        """
        Discover running backend instances.
        
        Returns:
            List of discovered backend instances
        """
        instances = []
        
        # Check for backend instances (backend, backend-2, backend-3, etc.)
        for i in range(1, self.max_instances + 1):
            instance_id = f"backend-{i}" if i > 1 else "backend"
            host = instance_id
            port = 8000
            
            instance = BackendInstance(
                instance_id=instance_id,
                host=host,
                port=port,
                status='unknown',
                health='unknown'
            )
            
            # Check if instance is healthy
            is_healthy = await self.check_backend_health(instance)
            if is_healthy:
                instance.status = 'running'
                instances.append(instance)
                logger.info(f"Discovered healthy instance: {instance_id}")
        
        return instances
    
    def calculate_load(self, metrics: SystemMetrics) -> float:
        """
        Calculate overall system load from metrics.
        
        Uses weighted average of CPU and memory usage.
        
        Args:
            metrics: System metrics
        
        Returns:
            Load value between 0 and 1
        """
        # Weight CPU more heavily than memory for scaling decisions
        cpu_weight = 0.7
        memory_weight = 0.3
        
        load = (
            (metrics.cpu_percent / 100.0) * cpu_weight +
            (metrics.memory_percent / 100.0) * memory_weight
        )
        
        return load
    
    def should_scale_up(self, load: float, current_instances: int) -> bool:
        """
        Determine if system should scale up.
        
        Args:
            load: Current system load (0-1)
            current_instances: Current number of instances
        
        Returns:
            True if should scale up
        """
        # Don't scale up if at max instances
        if current_instances >= self.max_instances:
            return False
        
        # Scale up if load exceeds threshold
        if load >= self.scale_up_threshold:
            return True
        
        return False
    
    def should_scale_down(self, load: float, current_instances: int) -> bool:
        """
        Determine if system should scale down.
        
        Args:
            load: Current system load (0-1)
            current_instances: Current number of instances
        
        Returns:
            True if should scale down
        """
        # Don't scale down if at min instances
        if current_instances <= self.min_instances:
            return False
        
        # Scale down if load is below threshold
        if load <= self.scale_down_threshold:
            return True
        
        return False
    
    def is_in_cooldown(self) -> bool:
        """
        Check if system is in cooldown period.
        
        Returns:
            True if in cooldown period
        """
        if self.last_scaling_action is None:
            return False
        
        elapsed = (datetime.now() - self.last_scaling_action).total_seconds()
        return elapsed < self.cooldown_period
    
    async def make_scaling_decision(self) -> ScalingDecision:
        """
        Analyze metrics and make scaling decision.
        
        Returns:
            ScalingDecision with action to take
        """
        # Get current metrics
        metrics = await self.get_system_metrics()
        
        # Discover current instances
        instances = await self.discover_instances()
        current_instances = len(instances)
        
        # Calculate load
        load = self.calculate_load(metrics)
        
        logger.info(
            f"Current load: {load:.2%} "
            f"(CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_percent:.1f}%) "
            f"Instances: {current_instances}"
        )
        
        # Check if in cooldown
        if self.is_in_cooldown():
            cooldown_remaining = self.cooldown_period - (
                datetime.now() - self.last_scaling_action
            ).total_seconds()
            return ScalingDecision(
                action='no_action',
                reason=f'In cooldown period ({cooldown_remaining:.0f}s remaining)',
                current_instances=current_instances,
                target_instances=current_instances,
                metrics=metrics
            )
        
        # Determine scaling action
        if self.should_scale_up(load, current_instances):
            target_instances = min(current_instances + 1, self.max_instances)
            return ScalingDecision(
                action='scale_up',
                reason=f'Load {load:.2%} exceeds threshold {self.scale_up_threshold:.2%}',
                current_instances=current_instances,
                target_instances=target_instances,
                metrics=metrics
            )
        
        elif self.should_scale_down(load, current_instances):
            target_instances = max(current_instances - 1, self.min_instances)
            return ScalingDecision(
                action='scale_down',
                reason=f'Load {load:.2%} below threshold {self.scale_down_threshold:.2%}',
                current_instances=current_instances,
                target_instances=target_instances,
                metrics=metrics
            )
        
        else:
            return ScalingDecision(
                action='no_action',
                reason=f'Load {load:.2%} within acceptable range',
                current_instances=current_instances,
                target_instances=current_instances,
                metrics=metrics
            )
    
    async def scale_up(self, target_instances: int) -> bool:
        """
        Scale up by adding backend instances.
        
        Args:
            target_instances: Target number of instances
        
        Returns:
            True if successful
        """
        current_instances = len(await self.discover_instances())
        instances_to_add = target_instances - current_instances
        
        logger.info(f"Scaling up: adding {instances_to_add} instance(s)")
        
        try:
            # Start new backend instances using docker-compose
            for i in range(instances_to_add):
                next_id = current_instances + i + 1
                instance_name = f"backend-{next_id}" if next_id > 1 else "backend"
                
                # Start instance
                cmd = f"docker-compose -f {self.docker_compose_path} up -d {instance_name}"
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Failed to start {instance_name}: {stderr.decode()}")
                    return False
                
                logger.info(f"Started instance: {instance_name}")
                
                # Wait for instance to be healthy
                await asyncio.sleep(10)
            
            # Reload Nginx configuration
            await self.reload_nginx()
            
            self.last_scaling_action = datetime.now()
            logger.info(f"Successfully scaled up to {target_instances} instances")
            return True
        
        except Exception as e:
            logger.error(f"Error scaling up: {e}")
            return False
    
    async def scale_down(self, target_instances: int) -> bool:
        """
        Scale down by removing backend instances.
        
        Args:
            target_instances: Target number of instances
        
        Returns:
            True if successful
        """
        instances = await self.discover_instances()
        current_instances = len(instances)
        instances_to_remove = current_instances - target_instances
        
        logger.info(f"Scaling down: removing {instances_to_remove} instance(s)")
        
        try:
            # Remove instances in reverse order (highest ID first)
            instances_sorted = sorted(instances, key=lambda x: x.instance_id, reverse=True)
            
            for i in range(instances_to_remove):
                instance = instances_sorted[i]
                
                # Stop instance
                cmd = f"docker-compose -f {self.docker_compose_path} stop {instance.instance_id}"
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Failed to stop {instance.instance_id}: {stderr.decode()}")
                    return False
                
                logger.info(f"Stopped instance: {instance.instance_id}")
            
            # Reload Nginx configuration
            await self.reload_nginx()
            
            self.last_scaling_action = datetime.now()
            logger.info(f"Successfully scaled down to {target_instances} instances")
            return True
        
        except Exception as e:
            logger.error(f"Error scaling down: {e}")
            return False
    
    async def reload_nginx(self) -> bool:
        """
        Reload Nginx configuration.
        
        Returns:
            True if successful
        """
        try:
            cmd = "docker-compose exec -T nginx nginx -s reload"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to reload Nginx: {stderr.decode()}")
                return False
            
            logger.info("Nginx configuration reloaded")
            return True
        
        except Exception as e:
            logger.error(f"Error reloading Nginx: {e}")
            return False
    
    async def execute_scaling_decision(self, decision: ScalingDecision) -> bool:
        """
        Execute a scaling decision.
        
        Args:
            decision: Scaling decision to execute
        
        Returns:
            True if successful
        """
        if decision.action == 'no_action':
            return True
        
        logger.info(
            f"Executing scaling decision: {decision.action} "
            f"({decision.current_instances} -> {decision.target_instances}) "
            f"Reason: {decision.reason}"
        )
        
        if decision.action == 'scale_up':
            return await self.scale_up(decision.target_instances)
        elif decision.action == 'scale_down':
            return await self.scale_down(decision.target_instances)
        
        return False
    
    async def run(self):
        """
        Run the auto-scaling service.
        
        This is the main loop that continuously monitors metrics and scales instances.
        """
        self.running = True
        logger.info("Auto-scaler started")
        logger.info(
            f"Configuration: min={self.min_instances}, max={self.max_instances}, "
            f"scale_up_threshold={self.scale_up_threshold:.2%}, "
            f"scale_down_threshold={self.scale_down_threshold:.2%}, "
            f"cooldown={self.cooldown_period}s, check_interval={self.check_interval}s"
        )
        
        while self.running:
            try:
                # Make scaling decision
                decision = await self.make_scaling_decision()
                
                # Execute decision
                if decision.action != 'no_action':
                    success = await self.execute_scaling_decision(decision)
                    if not success:
                        logger.error("Failed to execute scaling decision")
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Error in auto-scaling loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the auto-scaling service."""
        logger.info("Stopping auto-scaler")
        self.running = False


async def main():
    """Main entry point for auto-scaler service."""
    # Get configuration from environment variables
    prometheus_url = os.getenv('PROMETHEUS_URL', 'http://prometheus:9090')
    min_instances = int(os.getenv('MIN_INSTANCES', '1'))
    max_instances = int(os.getenv('MAX_INSTANCES', '10'))
    scale_up_threshold = float(os.getenv('SCALE_UP_THRESHOLD', '0.80'))
    scale_down_threshold = float(os.getenv('SCALE_DOWN_THRESHOLD', '0.30'))
    cooldown_period = int(os.getenv('COOLDOWN_PERIOD', '300'))
    check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    
    # Create and run auto-scaler
    autoscaler = AutoScaler(
        prometheus_url=prometheus_url,
        min_instances=min_instances,
        max_instances=max_instances,
        scale_up_threshold=scale_up_threshold,
        scale_down_threshold=scale_down_threshold,
        cooldown_period=cooldown_period,
        check_interval=check_interval
    )
    
    try:
        await autoscaler.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        autoscaler.stop()


if __name__ == '__main__':
    asyncio.run(main())
