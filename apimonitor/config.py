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
        
        # Convert to dict for serialization without Python-specific types
        data = self._to_serializable_dict()
        
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
    
    def _to_serializable_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with simple types for serialization"""
        data = {}
        
        # Copy basic fields
        for field_name, field_value in self.__dict__.items():
            if field_name in ['endpoints', 'notifications']:
                continue
            data[field_name] = field_value
        
        # Convert endpoints
        data['endpoints'] = []
        for endpoint in self.endpoints:
            endpoint_dict = endpoint.dict()
            # Convert enum to string
            if 'method' in endpoint_dict:
                endpoint_dict['method'] = endpoint_dict['method'].value if hasattr(endpoint_dict['method'], 'value') else str(endpoint_dict['method'])
            data['endpoints'].append(endpoint_dict)
        
        # Convert notifications
        data['notifications'] = {}
        for name, notification in self.notifications.items():
            notif_dict = notification.dict()
            # Convert enum to string
            if 'type' in notif_dict:
                notif_dict['type'] = notif_dict['type'].value if hasattr(notif_dict['type'], 'value') else str(notif_dict['type'])
            data['notifications'][name] = notif_dict
        
        return data
    
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
