"""
Data models for ApiMonitor
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HttpMethod(str, Enum):
    """HTTP method enumeration"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"


class NotificationType(str, Enum):
    """Notification type enumeration"""
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"


class CheckResult(BaseModel):
    """Result of a single health check"""
    endpoint_id: str
    timestamp: datetime
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    success: bool
    health_status: HealthStatus
    response_body: Optional[str] = None
    response_headers: Optional[Dict[str, str]] = None


class EndpointStats(BaseModel):
    """Statistics for an endpoint"""
    endpoint_id: str
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    uptime_percentage: float = 100.0
    last_check: Optional[datetime] = None
    current_status: HealthStatus = HealthStatus.UNKNOWN
    
    def update_stats(self, result: CheckResult):
        """Update statistics with new check result"""
        self.total_checks += 1
        self.last_check = result.timestamp
        self.current_status = result.health_status
        
        if result.success and result.response_time_ms is not None:
            self.successful_checks += 1
            
            # Update response time stats
            if self.average_response_time == 0:
                self.average_response_time = result.response_time_ms
            else:
                self.average_response_time = (
                    (self.average_response_time * (self.successful_checks - 1) + result.response_time_ms) 
                    / self.successful_checks
                )
            
            self.min_response_time = min(self.min_response_time, result.response_time_ms)
            self.max_response_time = max(self.max_response_time, result.response_time_ms)
        else:
            self.failed_checks += 1
        
        # Calculate uptime percentage
        self.uptime_percentage = (self.successful_checks / self.total_checks) * 100


class NotificationConfig(BaseModel):
    """Notification configuration"""
    type: NotificationType
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Notification triggers
    on_failure: bool = True
    on_recovery: bool = True
    on_degraded: bool = False
    
    # Rate limiting
    max_notifications_per_hour: int = 10
    cooldown_minutes: int = 5


class EndpointConfig(BaseModel):
    """Configuration for a monitored endpoint"""
    id: str
    url: str
    method: HttpMethod = HttpMethod.GET
    timeout_seconds: float = 10.0
    
    # Request configuration
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None
    params: Dict[str, str] = Field(default_factory=dict)
    
    # Health check configuration
    expected_status_codes: List[int] = Field(default_factory=lambda: [200])
    expected_response_time_ms: Optional[float] = None
    response_contains: Optional[str] = None
    response_not_contains: Optional[str] = None
    
    # Monitoring configuration
    check_interval_seconds: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # SLA configuration
    sla_uptime_percentage: float = 99.9
    sla_response_time_ms: Optional[float] = None
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            # Auto-add https:// if no protocol specified
            v = f"https://{v}"
        return v
    
    @validator('check_interval_seconds')
    def validate_interval(cls, v):
        if v < 10:
            raise ValueError('Check interval must be at least 10 seconds')
        return v
