"""
Tests for endpoint monitoring
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from apimonitor.endpoint import Endpoint
from apimonitor.models import EndpointConfig, HealthStatus, HttpMethod


class TestEndpoint:
    
    @pytest.mark.asyncio
    async def test_endpoint_creation(self, sample_endpoint_config):
        """Test endpoint creation"""
        endpoint = Endpoint(sample_endpoint_config)
        
        assert endpoint.id == "test_endpoint"
        assert endpoint.url == "https://httpbin.org/status/200"
        assert not endpoint.is_monitoring
    
    @pytest.mark.asyncio
    async def test_session_management(self, sample_endpoint_config):
        """Test HTTP session management"""
        endpoint = Endpoint(sample_endpoint_config)
        
        # Start session
        await endpoint.start_session()
        assert endpoint._session is not None
        
        # Close session
        await endpoint.close_session()
        assert endpoint._session is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, sample_endpoint_config):
        """Test endpoint as context manager"""
        endpoint = Endpoint(sample_endpoint_config)
        
        async with endpoint:
            assert endpoint._session is not None
        
        assert endpoint._session is None
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        config = EndpointConfig(
            id="test",
            url="https://httpbin.org/status/200",
            timeout_seconds=10
        )
        
        endpoint = Endpoint(config)
        
        try:
            result = await endpoint.check_health()
            
            assert result.endpoint_id == "test"
            assert result.success == True
            assert result.status_code == 200
            assert result.health_status == HealthStatus.HEALTHY
            assert result.response_time_ms is not None
            assert result.response_time_ms > 0
            
        finally:
            await endpoint.close_session()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        config = EndpointConfig(
            id="test",
            url="https://httpbin.org/status/500",
            timeout_seconds=10,
            expected_status_codes=[200]
        )
        
        endpoint = Endpoint(config)
        
        try:
            result = await endpoint.check_health()
            
            assert result.endpoint_id == "test"
            assert result.success == False
            assert result.status_code == 500
            assert result.health_status == HealthStatus.UNHEALTHY
            
        finally:
            await endpoint.close_session()
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check timeout"""
        config = EndpointConfig(
            id="test",
            url="https://httpbin.org/delay/10",  # 10 second delay
            timeout_seconds=2  # 2 second timeout
        )
        
        endpoint = Endpoint(config)
        
        try:
            result = await endpoint.check_health()
            
            assert result.endpoint_id == "test"
            assert result.success == False
            assert result.health_status == HealthStatus.UNHEALTHY
            assert result.error_message is not None
            
        finally:
            await endpoint.close_session()
    
    @pytest.mark.asyncio
    async def test_response_time_evaluation(self):
        """Test response time-based health evaluation"""
        config = EndpointConfig(
            id="test",
            url="https://httpbin.org/delay/1",
            timeout_seconds=5,
            expected_response_time_ms=500  # Expect under 500ms
        )
        
        endpoint = Endpoint(config)
        
        try:
            result = await endpoint.check_health()
            
            assert result.endpoint_id == "test"
            assert result.status_code == 200
            # Should be degraded due to slow response
            assert result.health_status in [HealthStatus.DEGRADED, HealthStatus.HEALTHY]
            
        finally:
            await endpoint.close_session()
    
    @pytest.mark.asyncio
    async def test_response_content_evaluation(self):
        """Test response content-based health evaluation"""
        config = EndpointConfig(
            id="test",
            url="https://httpbin.org/json",
            timeout_seconds=10,
            response_contains="slideshow"  # httpbin.org/json contains this
        )
        
        endpoint = Endpoint(config)
        
        try:
            result = await endpoint.check_health()
            
            assert result.endpoint_id == "test"
            assert result.success == True
            assert result.health_status == HealthStatus.HEALTHY
            
        finally:
            await endpoint.close_session()
    
    @pytest.mark.asyncio
    async def test_monitoring_start_stop(self, sample_endpoint_config):
        """Test starting and stopping monitoring"""
        endpoint = Endpoint(sample_endpoint_config)
        
        # Start monitoring
        callback_results = []
        
        def callback(result):
            callback_results.append(result)
        
        await endpoint.start_monitoring(callback)
        assert endpoint.is_monitoring
        
        # Wait a bit for monitoring to run
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await endpoint.stop_monitoring()
        assert not endpoint.is_monitoring
        
        await endpoint.close_session()