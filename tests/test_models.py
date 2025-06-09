"""
Tests for ApiMonitor data models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from apimonitor.models import (
    EndpointConfig, NotificationConfig, CheckResult, 
    EndpointStats, HealthStatus, HttpMethod, NotificationType
)


class TestEndpointConfig:
    
    def test_valid_endpoint_config(self):
        """Test creating valid endpoint configuration"""
        config = EndpointConfig(
            id="test",
            url="https://example.com",
            method=HttpMethod.GET,
            timeout_seconds=10,
            check_interval_seconds=300
        )
        
        assert config.id == "test"
        assert config.url == "https://example.com"
        assert config.method == HttpMethod.GET
        assert config.timeout_seconds == 10
        assert config.check_interval_seconds == 300
        assert config.expected_status_codes == [200]
    
    def test_invalid_url(self):
        """Test invalid URL validation"""
        # Test truly invalid URLs (protocol gets auto-added for most URLs)
        with pytest.raises(ValidationError):
            EndpointConfig(
                id="test",
                url="",  # Empty URL should fail
                method=HttpMethod.GET
            )
    
    def test_invalid_interval(self):
        """Test invalid check interval validation"""
        with pytest.raises(ValidationError):
            EndpointConfig(
                id="test",
                url="https://example.com",
                check_interval_seconds=5  # Too low
            )
    
    def test_auto_add_protocol(self):
        """Test URL protocol auto-addition"""
        config = EndpointConfig(
            id="test",
            url="example.com",
            method=HttpMethod.GET
        )
        # Auto-adds https:// protocol
        assert config.url == "https://example.com"


class TestNotificationConfig:
    
    def test_valid_notification_config(self):
        """Test creating valid notification configuration"""
        config = NotificationConfig(
            type=NotificationType.SLACK,
            enabled=True,
            config={"webhook_url": "https://hooks.slack.com/test"},
            on_failure=True,
            on_recovery=True
        )
        
        assert config.type == NotificationType.SLACK
        assert config.enabled == True
        assert config.on_failure == True
        assert config.on_recovery == True
        assert config.config["webhook_url"] == "https://hooks.slack.com/test"


class TestCheckResult:
    
    def test_successful_check_result(self):
        """Test creating successful check result"""
        result = CheckResult(
            endpoint_id="test",
            timestamp=datetime.now(),
            status_code=200,
            response_time_ms=150.5,
            success=True,
            health_status=HealthStatus.HEALTHY
        )
        
        assert result.endpoint_id == "test"
        assert result.status_code == 200
        assert result.response_time_ms == 150.5
        assert result.success == True
        assert result.health_status == HealthStatus.HEALTHY
    
    def test_failed_check_result(self):
        """Test creating failed check result"""
        result = CheckResult(
            endpoint_id="test",
            timestamp=datetime.now(),
            error_message="Connection timeout",
            success=False,
            health_status=HealthStatus.UNHEALTHY
        )
        
        assert result.endpoint_id == "test"
        assert result.error_message == "Connection timeout"
        assert result.success == False
        assert result.health_status == HealthStatus.UNHEALTHY


class TestEndpointStats:
    
    def test_initial_stats(self):
        """Test initial endpoint statistics"""
        stats = EndpointStats(endpoint_id="test")
        
        assert stats.endpoint_id == "test"
        assert stats.total_checks == 0
        assert stats.successful_checks == 0
        assert stats.failed_checks == 0
        assert stats.uptime_percentage == 100.0
        assert stats.current_status == HealthStatus.UNKNOWN
    
    def test_update_stats_success(self):
        """Test updating stats with successful result"""
        stats = EndpointStats(endpoint_id="test")
        
        result = CheckResult(
            endpoint_id="test",
            timestamp=datetime.now(),
            status_code=200,
            response_time_ms=100.0,
            success=True,
            health_status=HealthStatus.HEALTHY
        )
        
        stats.update_stats(result)
        
        assert stats.total_checks == 1
        assert stats.successful_checks == 1
        assert stats.failed_checks == 0
        assert stats.uptime_percentage == 100.0
        assert stats.average_response_time == 100.0
        assert stats.min_response_time == 100.0
        assert stats.max_response_time == 100.0
        assert stats.current_status == HealthStatus.HEALTHY
    
    def test_update_stats_failure(self):
        """Test updating stats with failed result"""
        stats = EndpointStats(endpoint_id="test")
        
        result = CheckResult(
            endpoint_id="test",
            timestamp=datetime.now(),
            error_message="Failed",
            success=False,
            health_status=HealthStatus.UNHEALTHY
        )
        
        stats.update_stats(result)
        
        assert stats.total_checks == 1
        assert stats.successful_checks == 0
        assert stats.failed_checks == 1
        assert stats.uptime_percentage == 0.0
        assert stats.current_status == HealthStatus.UNHEALTHY
