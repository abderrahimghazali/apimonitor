# apimonitor/config.py
"""
Configuration management for ApiMonitor
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator

from .models import EndpointConfig, NotificationConfig, NotificationType
from .exceptions import ConfigurationError


class MonitorConfig(BaseModel):
    """Main configuration for ApiMonitor"""
    
    # Global settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    data_dir: str = "./apimonitor_data"
    max_history_days: int = 30
    
    # Default endpoint settings
    default_timeout: float = 10.0
    default_interval: int = 300  # 5 minutes
    default_retries: int = 3
    
    # Dashboard settings
    dashboard_enabled: bool = False
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8080
    dashboard_auth: Optional[Dict[str, str]] = None
    
    # Endpoints and notifications
    endpoints: List[EndpointConfig] = Field(default_factory=list)
    notifications: Dict[str, NotificationConfig] = Field(default_factory=dict)
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('max_history_days')
    def validate_history_days(cls, v):
        if v < 1:
            raise ValueError('max_history_days must be at least 1')
        return v
    
    def add_endpoint(self, endpoint: EndpointConfig):
        """Add an endpoint to monitor"""
        # Check for duplicate IDs
        existing_ids = [ep.id for ep in self.endpoints]
        if endpoint.id in existing_ids:
            raise ConfigurationError(f"Endpoint ID '{endpoint.id}' already exists")
        
        self.endpoints.append(endpoint)
    
    def add_notification(self, name: str, notification: NotificationConfig):
        """Add a notification channel"""
        self.notifications[name] = notification
    
    def get_endpoint(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """Get endpoint by ID"""
        for endpoint in self.endpoints:
            if endpoint.id == endpoint_id:
                return endpoint
        return None
    
    def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove endpoint by ID"""
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.id == endpoint_id:
                del self.endpoints[i]
                return True
        return False
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'MonitorConfig':
        """Load configuration from file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
            
            return cls.parse_config_data(data)
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading config file: {e}")
    
    @classmethod
    def parse_config_data(cls, data: Dict[str, Any]) -> 'MonitorConfig':
        """Parse configuration data from dictionary"""
        try:
            # Parse endpoints
            endpoints = []
            for ep_data in data.get('endpoints', []):
                endpoints.append(EndpointConfig(**ep_data))
            
            # Parse notifications
            notifications = {}
            for name, notif_data in data.get('notifications', {}).items():
                notifications[name] = NotificationConfig(**notif_data)
            
            # Create config
            config_data = {**data}
            config_data['endpoints'] = endpoints
            config_data['notifications'] = notifications
            
            return cls(**config_data)
            
        except Exception as e:
            raise ConfigurationError(f"Error parsing configuration: {e}")
    
    def to_file(self, file_path: Union[str, Path]):
        """Save configuration to file"""
        file_path = Path(file_path)
        
        # Convert to dict for serialization
        data = self.dict()
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2, default=str)
                else:
                    raise ConfigurationError(f"Unsupported file format: {file_path.suffix}")
                    
        except Exception as e:
            raise ConfigurationError(f"Error writing config file: {e}")
    
    @classmethod
    def create_example_config(cls) -> 'MonitorConfig':
        """Create an example configuration"""
        
        # Example endpoints
        endpoints = [
            EndpointConfig(
                id="api_health",
                url="https://httpbin.org/status/200",
                method="GET",
                check_interval_seconds=60,
                expected_status_codes=[200],
                timeout_seconds=5.0
            ),
            EndpointConfig(
                id="api_slow",
                url="https://httpbin.org/delay/2",
                method="GET",
                check_interval_seconds=300,
                expected_status_codes=[200],
                sla_response_time_ms=3000,
                timeout_seconds=10.0
            )
        ]
        
        # Example notifications
        notifications = {
            "console": NotificationConfig(
                type=NotificationType.CONSOLE,
                enabled=True,
                on_failure=True,
                on_recovery=True
            ),
            "slack": NotificationConfig(
                type=NotificationType.SLACK,
                enabled=False,
                config={
                    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
                },
                on_failure=True,
                on_recovery=True,
                max_notifications_per_hour=5
            )
        }
        
        return cls(
            endpoints=endpoints,
            notifications=notifications,
            dashboard_enabled=True,
            log_level="INFO"
        )


def load_config_from_env() -> MonitorConfig:
    """Load configuration from environment variables"""
    config_file = os.getenv('APIMONITOR_CONFIG')
    if config_file:
        return MonitorConfig.from_file(config_file)
    
    # Create basic config from environment
    endpoints = []
    
    # Simple single endpoint from env
    url = os.getenv('APIMONITOR_URL')
    if url:
        endpoint = EndpointConfig(
            id="env_endpoint",
            url=url,
            timeout_seconds=float(os.getenv('APIMONITOR_TIMEOUT', '10')),
            check_interval_seconds=int(os.getenv('APIMONITOR_INTERVAL', '300'))
        )
        endpoints.append(endpoint)
    
    # Notifications
    notifications = {}
    
    # Console notification (always enabled)
    notifications["console"] = NotificationConfig(
        type=NotificationType.CONSOLE,
        enabled=True
    )
    
    # Slack notification from env
    slack_webhook = os.getenv('APIMONITOR_SLACK_WEBHOOK')
    if slack_webhook:
        notifications["slack"] = NotificationConfig(
            type=NotificationType.SLACK,
            enabled=True,
            config={"webhook_url": slack_webhook}
        )
    
    return MonitorConfig(
        endpoints=endpoints,
        notifications=notifications,
        log_level=os.getenv('APIMONITOR_LOG_LEVEL', 'INFO'),
        dashboard_enabled=os.getenv('APIMONITOR_DASHBOARD', 'false').lower() == 'true'
    )


# apimonitor/monitor.py
"""
Main ApiMonitor class
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from .config import MonitorConfig
from .endpoint import Endpoint
from .models import CheckResult, EndpointStats, HealthStatus
from .notifications import NotificationManager
from .exceptions import ApiMonitorError


class ApiMonitor:
    """
    Main API monitoring class
    
    Examples:
        Basic usage:
        >>> monitor = ApiMonitor()
        >>> monitor.add_endpoint("https://api.example.com/health", "api_health")
        >>> monitor.start()
        
        With configuration file:
        >>> monitor = ApiMonitor.from_config("config.yaml")
        >>> monitor.start()
        
        Programmatic monitoring:
        >>> async with ApiMonitor() as monitor:
        ...     result = await monitor.check_endpoint("api_health")
        ...     print(f"Status: {result.health_status}")
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self.endpoints: Dict[str, Endpoint] = {}
        self.notification_manager = NotificationManager()
        self.results_history: List[CheckResult] = []
        self.stats: Dict[str, EndpointStats] = {}
        self._monitoring = False
        self._tasks: List[asyncio.Task] = []
        self._logger: Optional[logging.Logger] = None
        
        # Setup from config
        self._setup_logging()
        self._setup_endpoints()
        self._setup_notifications()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self._logger = logging.getLogger('apimonitor')
        self._logger.setLevel(getattr(logging, self.config.log_level))
        
        # Remove existing handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
        
        # File handler if specified
        if self.config.log_file:
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(console_formatter)
            self._logger.addHandler(file_handler)
    
    def _setup_endpoints(self):
        """Setup endpoints from configuration"""
        for endpoint_config in self.config.endpoints:
            endpoint = Endpoint(endpoint_config)
            self.endpoints[endpoint_config.id] = endpoint
            self.stats[endpoint_config.id] = EndpointStats(endpoint_id=endpoint_config.id)
    
    def _setup_notifications(self):
        """Setup notification channels from configuration"""
        for name, notif_config in self.config.notifications.items():
            self.notification_manager.add_channel(name, notif_config)
    
    @classmethod
    def from_config(cls, config_path: str) -> 'ApiMonitor':
        """Create ApiMonitor from configuration file"""
        config = MonitorConfig.from_file(config_path)
        return cls(config)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ApiMonitor':
        """Create ApiMonitor from configuration dictionary"""
        config = MonitorConfig.parse_config_data(config_dict)
        return cls(config)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_sessions()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
        await self.close_sessions()
    
    async def start_sessions(self):
        """Start HTTP sessions for all endpoints"""
        for endpoint in self.endpoints.values():
            await endpoint.start_session()
    
    async def close_sessions(self):
        """Close HTTP sessions for all endpoints"""
        for endpoint in self.endpoints.values():
            await endpoint.close_session()
    
    def add_endpoint(self, url: str, endpoint_id: str, **kwargs):
        """
        Add an endpoint to monitor
        
        Args:
            url: Endpoint URL
            endpoint_id: Unique identifier
            **kwargs: Additional endpoint configuration
        """
        from .models import EndpointConfig
        
        # Use defaults from config
        defaults = {
            'timeout_seconds': self.config.default_timeout,
            'check_interval_seconds': self.config.default_interval,
            'max_retries': self.config.default_retries,
        }
        defaults.update(kwargs)
        
        endpoint_config = EndpointConfig(
            id=endpoint_id,
            url=url,
            **defaults
        )
        
        endpoint = Endpoint(endpoint_config)
        self.endpoints[endpoint_id] = endpoint
        self.stats[endpoint_id] = EndpointStats(endpoint_id=endpoint_id)
        
        self._logger.info(f"Added endpoint: {endpoint_id} -> {url}")
    
    def remove_endpoint(self, endpoint_id: str):
        """Remove an endpoint from monitoring"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            del self.stats[endpoint_id]
            self._logger.info(f"Removed endpoint: {endpoint_id}")
    
    def add_notification_channel(self, name: str, notification_type: str, config: Dict[str, Any]):
        """Add a notification channel"""
        from .models import NotificationConfig, NotificationType
        
        notif_config = NotificationConfig(
            type=NotificationType(notification_type),
            config=config
        )
        
        self.notification_manager.add_channel(name, notif_config)
        self._logger.info(f"Added notification channel: {name} ({notification_type})")
    
    async def check_endpoint(self, endpoint_id: str) -> CheckResult:
        """
        Perform a single health check on an endpoint
        
        Args:
            endpoint_id: ID of endpoint to check
            
        Returns:
            CheckResult object
        """
        if endpoint_id not in self.endpoints:
            raise ApiMonitorError(f"Endpoint not found: {endpoint_id}")
        
        endpoint = self.endpoints[endpoint_id]
        result = await endpoint.check_health()
        
        # Store result
        self.results_history.append(result)
        self.stats[endpoint_id] = endpoint.stats
        
        # Send notifications if needed
        await self._handle_result(result)
        
        return result
    
    async def check_all_endpoints(self) -> List[CheckResult]:
        """Check all endpoints once"""
        tasks = []
        for endpoint_id in self.endpoints:
            tasks.append(self.check_endpoint(endpoint_id))
        
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def start(self, background: bool = False):
        """
        Start monitoring all endpoints
        
        Args:
            background: If True, run in background tasks
        """
        if self._monitoring:
            self._logger.warning("Monitoring already started")
            return
        
        self._monitoring = True
        self._logger.info("Starting API monitoring...")
        
        # Start sessions
        await self.start_sessions()
        
        if background:
            # Start background tasks
            for endpoint_id, endpoint in self.endpoints.items():
                task = asyncio.create_task(
                    self._monitor_endpoint(endpoint_id, endpoint)
                )
                self._tasks.append(task)
        else:
            # Run monitoring loop
            await self._monitoring_loop()
    
    async def stop(self):
        """Stop monitoring"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        self._logger.info("Stopping API monitoring...")
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
        
        # Stop endpoint monitoring
        for endpoint in self.endpoints.values():
            await endpoint.stop_monitoring()
    
    async def _monitoring_loop(self):
        """Main monitoring loop for non-background mode"""
        try:
            while self._monitoring:
                # Check all endpoints
                await self.check_all_endpoints()
                
                # Wait for next cycle (use minimum interval)
                min_interval = min(
                    [ep.config.check_interval_seconds for ep in self.endpoints.values()],
                    default=60
                )
                
                await asyncio.sleep(min_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._logger.error(f"Error in monitoring loop: {e}")
        finally:
            self._monitoring = False
    
    async def _monitor_endpoint(self, endpoint_id: str, endpoint: Endpoint):
        """Monitor a single endpoint in background"""
        try:
            await endpoint.start_monitoring(callback=self._handle_result)
        except Exception as e:
            self._logger.error(f"Error monitoring endpoint {endpoint_id}: {e}")
    
    async def _handle_result(self, result: CheckResult):
        """Handle a check result"""
        # Update stats
        if result.endpoint_id in self.stats:
            self.stats[result.endpoint_id].update_stats(result)
        
        # Log result
        log_level = {
            HealthStatus.HEALTHY: logging.INFO,
            HealthStatus.DEGRADED: logging.WARNING,
            HealthStatus.UNHEALTHY: logging.ERROR,
            HealthStatus.UNKNOWN: logging.WARNING
        }.get(result.health_status, logging.INFO)
        
        message = f"Endpoint {result.endpoint_id}: {result.health_status.value.upper()}"
        if result.response_time_ms:
            message += f" ({result.response_time_ms:.1f}ms)"
        if result.error_message:
            message += f" - {result.error_message}"
        
        self._logger.log(log_level, message)
        
        # Send notifications
        await self.notification_manager.send_notification(result, message)
        
        # Cleanup old results
        self._cleanup_history()
    
    def _cleanup_history(self):
        """Remove old results from history"""
        cutoff_date = datetime.now() - timedelta(days=self.config.max_history_days)
        
        # Keep results newer than cutoff
        self.results_history = [
            result for result in self.results_history
            if result.timestamp > cutoff_date
        ]
        
        # Keep only last 10000 results to prevent memory issues
        if len(self.results_history) > 10000:
            self.results_history = self.results_history[-10000:]
    
    def get_endpoint_stats(self, endpoint_id: str) -> Optional[EndpointStats]:
        """Get statistics for an endpoint"""
        return self.stats.get(endpoint_id)
    
    def get_all_stats(self) -> Dict[str, EndpointStats]:
        """Get statistics for all endpoints"""
        return self.stats.copy()
    
    def get_recent_results(self, endpoint_id: str = None, hours: int = 24) -> List[CheckResult]:
        """Get recent results for an endpoint or all endpoints"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        results = [
            result for result in self.results_history
            if result.timestamp > cutoff_time
        ]
        
        if endpoint_id:
            results = [
                result for result in results
                if result.endpoint_id == endpoint_id
            ]
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        total_endpoints = len(self.endpoints)
        if total_endpoints == 0:
            return {"status": "no_endpoints", "endpoints": 0}
        
        healthy = sum(1 for stats in self.stats.values() 
                     if stats.current_status == HealthStatus.HEALTHY)
        degraded = sum(1 for stats in self.stats.values() 
                      if stats.current_status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for stats in self.stats.values() 
                       if stats.current_status == HealthStatus.UNHEALTHY)
        
        # Overall status
        if unhealthy > 0:
            overall_status = "unhealthy"
        elif degraded > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "endpoints": total_endpoints,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "average_uptime": sum(stats.uptime_percentage for stats in self.stats.values()) / total_endpoints if total_endpoints > 0 else 0,
            "last_check": max((stats.last_check for stats in self.stats.values() if stats.last_check), default=None)
        }
    
    def export_data(self, file_path: str, format: str = "json"):
        """Export monitoring data"""
        data = {
            "config": self.config.dict(),
            "stats": {k: v.dict() for k, v in self.stats.items()},
            "recent_results": [r.dict() for r in self.get_recent_results(hours=24)],
            "summary": self.get_health_summary(),
            "exported_at": datetime.now().isoformat()
        }
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        self._logger.info(f"Data exported to {file_path}")


# Quick usage functions
async def quick_check(url: str, timeout: float = 10.0) -> CheckResult:
    """
    Quick health check of a single URL
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        CheckResult object
    """
    from .models import EndpointConfig
    
    config = EndpointConfig(
        id="quick_check",
        url=url,
        timeout_seconds=timeout
    )
    
    endpoint = Endpoint(config)
    try:
        await endpoint.start_session()
        return await endpoint.check_health()
    finally:
        await endpoint.close_session()


def create_example_config(output_path: str = "apimonitor_config.yaml"):
    """Create an example configuration file"""
    config = MonitorConfig.create_example_config()
    config.to_file(output_path)
    print(f"Example configuration created: {output_path}")