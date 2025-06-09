"""
Tests for main ApiMonitor class
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from apimonitor.monitor import ApiMonitor, quick_check
from apimonitor.config import MonitorConfig
from apimonitor.models import EndpointConfig, HealthStatus


class TestApiMonitor:
    
    def test_monitor_creation(self, sample_monitor_config):
        """Test ApiMonitor creation"""
        monitor = ApiMonitor(sample_monitor_config)
        
        assert len(monitor.endpoints) == 1
        assert "test_endpoint" in monitor.endpoints
        assert len(monitor.stats) == 1
    
    def test_monitor_from_config_file(self, config_file):
        """Test creating monitor from config file"""
        monitor = ApiMonitor.from_config(config_file)
        
        assert len(monitor.endpoints) == 1
        assert "test_endpoint" in monitor.endpoints
    
    def test_add_endpoint(self):
        """Test adding endpoint to monitor"""
        monitor = ApiMonitor()
        
        monitor.add_endpoint("https://example.com", "test_ep")
        
        assert len(monitor.endpoints) == 1
        assert "test_ep" in monitor.endpoints
        assert monitor.endpoints["test_ep"].url == "https://example.com"
    
    def test_remove_endpoint(self):
        """Test removing endpoint from monitor"""
        monitor = ApiMonitor()
        monitor.add_endpoint("https://example.com", "test_ep")
        
        assert len(monitor.endpoints) == 1
        
        monitor.remove_endpoint("test_ep")
        
        assert len(monitor.endpoints) == 0
        assert "test_ep" not in monitor.stats
    
    @pytest.mark.asyncio
    async def test_check_endpoint(self):
        """Test checking single endpoint"""
        monitor = ApiMonitor()
        monitor.add_endpoint("https://httpbin.org/status/200", "test_ep")
        
        try:
            result = await monitor.check_endpoint("test_ep")
            
            assert result.endpoint_id == "test_ep"
            assert result.success == True
            assert result.status_code == 200
            
            # Check that stats were updated
            stats = monitor.get_endpoint_stats("test_ep")
            assert stats is not None
            assert stats.total_checks == 1
            
        finally:
            await monitor.close_sessions()
    
    @pytest.mark.asyncio
    async def test_check_nonexistent_endpoint(self):
        """Test checking nonexistent endpoint"""
        monitor = ApiMonitor()
        
        with pytest.raises(Exception):  # Should raise ApiMonitorError
            await monitor.check_endpoint("nonexistent")
    
    @pytest.mark.asyncio
    async def test_check_all_endpoints(self):
        """Test checking all endpoints"""
        monitor = ApiMonitor()
        monitor.add_endpoint("https://httpbin.org/status/200", "test1")
        monitor.add_endpoint("https://httpbin.org/status/201", "test2")
        
        try:
            results = await monitor.check_all_endpoints()
            
            assert len(results) == 2
            assert all(result.success for result in results)
            
        finally:
            await monitor.close_sessions()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test monitor as context manager"""
        config = MonitorConfig()
        
        async with ApiMonitor(config) as monitor:
            monitor.add_endpoint("https://httpbin.org/status/200", "test")
            result = await monitor.check_endpoint("test")
            assert result.success == True
    
    def test_get_health_summary_empty(self):
        """Test health summary with no endpoints"""
        monitor = ApiMonitor()
        
        summary = monitor.get_health_summary()
        
        assert summary["status"] == "no_endpoints"
        assert summary["endpoints"] == 0
    
    @pytest.mark.asyncio
    async def test_get_health_summary_with_data(self):
        """Test health summary with endpoint data"""
        monitor = ApiMonitor()
        monitor.add_endpoint("https://httpbin.org/status/200", "healthy")
        monitor.add_endpoint("https://httpbin.org/status/500", "unhealthy")
        
        try:
            # Generate some data
            await monitor.check_all_endpoints()
            
            summary = monitor.get_health_summary()
            
            assert summary["endpoints"] == 2
            assert "healthy" in str(summary["status"]) or "unhealthy" in str(summary["status"])
            
        finally:
            await monitor.close_sessions()
    
    def test_get_recent_results(self):
        """Test getting recent results"""
        monitor = ApiMonitor()
        
        # Initially empty
        results = monitor.get_recent_results()
        assert len(results) == 0
        
        # Filter by endpoint
        results = monitor.get_recent_results("nonexistent")
        assert len(results) == 0
    
    def test_export_data(self, temp_dir):
        """Test exporting monitoring data"""
        monitor = ApiMonitor()
        monitor.add_endpoint("https://example.com", "test")
        
        export_path = f"{temp_dir}/export.json"
        monitor.export_data(export_path)
        
        import json
        with open(export_path) as f:
            data = json.load(f)
        
        assert "config" in data
        assert "stats" in data
        assert "summary" in data
        assert "exported_at" in data


class TestQuickCheck:
    
    @pytest.mark.asyncio
    async def test_quick_check_success(self):
        """Test quick_check function with successful endpoint"""
        result = await quick_check("https://httpbin.org/status/200")
        
        assert result.success == True
        assert result.status_code == 200
        assert result.health_status == HealthStatus.HEALTHY
        assert result.response_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_quick_check_failure(self):
        """Test quick_check function with failing endpoint"""
        result = await quick_check("https://httpbin.org/status/500")
        
        assert result.success == False
        assert result.status_code == 500
        assert result.health_status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_quick_check_timeout(self):
        """Test quick_check function with timeout"""
        result = await quick_check("https://httpbin.org/delay/10", timeout=1)
        
        assert result.success == False
        assert result.health_status == HealthStatus.UNHEALTHY
        assert result.error_message is not None
