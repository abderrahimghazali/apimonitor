"""
Custom exceptions for ApiMonitor
"""

class ApiMonitorError(Exception):
    """Base exception for ApiMonitor"""
    pass

class EndpointError(ApiMonitorError):
    """Raised when endpoint monitoring fails"""
    pass

class NotificationError(ApiMonitorError):
    """Raised when notification delivery fails"""
    pass

class ConfigurationError(ApiMonitorError):
    """Raised when configuration is invalid"""
    pass