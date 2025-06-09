"""
Endpoint monitoring functionality
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Optional, Dict, Any

from .models import EndpointConfig, CheckResult, HealthStatus, EndpointStats
from .exceptions import EndpointError


class Endpoint:
    """
    Represents a monitored API endpoint
    """
    
    def __init__(self, config: EndpointConfig):
        self.config = config
        self.stats = EndpointStats(endpoint_id=config.id)
        self._session: Optional[aiohttp.ClientSession] = None
        self._monitoring = False
        self._task: Optional[asyncio.Task] = None
    
    @property
    def id(self) -> str:
        return self.config.id
    
    @property
    def url(self) -> str:
        return self.config.url
    
    @property
    def is_monitoring(self) -> bool:
        return self._monitoring
    
    async def __aenter__(self):
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
    
    async def start_session(self):
        """Start HTTP session"""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def check_health(self) -> CheckResult:
        """
        Perform a single health check
        
        Returns:
            CheckResult object with check details
        """
        if not self._session:
            await self.start_session()
        
        start_time = time.time()
        timestamp = datetime.now()
        
        try:
            # Prepare request
            kwargs = {
                'method': self.config.method.value,
                'url': self.config.url,
                'headers': self.config.headers,
                'params': self.config.params,
            }
            
            if self.config.body:
                kwargs['data'] = self.config.body
            
            # Make request with retries
            last_error = None
            for attempt in range(self.config.max_retries + 1):
                try:
                    async with self._session.request(**kwargs) as response:
                        response_time_ms = (time.time() - start_time) * 1000
                        response_text = await response.text()
                        response_headers = dict(response.headers)
                        
                        # Evaluate health status
                        health_status = self._evaluate_health(
                            response.status, 
                            response_time_ms, 
                            response_text
                        )
                        
                        result = CheckResult(
                            endpoint_id=self.config.id,
                            timestamp=timestamp,
                            status_code=response.status,
                            response_time_ms=response_time_ms,
                            success=health_status != HealthStatus.UNHEALTHY,
                            health_status=health_status,
                            response_body=response_text[:1000],  # Limit response body
                            response_headers=response_headers
                        )
                        
                        # Update statistics
                        self.stats.update_stats(result)
                        return result
                        
                except aiohttp.ClientError as e:
                    last_error = e
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(self.config.retry_delay_seconds)
                    continue
            
            # All retries failed
            response_time_ms = (time.time() - start_time) * 1000
            error_message = f"Failed after {self.config.max_retries + 1} attempts: {str(last_error)}"
            
            result = CheckResult(
                endpoint_id=self.config.id,
                timestamp=timestamp,
                response_time_ms=response_time_ms,
                error_message=error_message,
                success=False,
                health_status=HealthStatus.UNHEALTHY
            )
            
            self.stats.update_stats(result)
            return result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            result = CheckResult(
                endpoint_id=self.config.id,
                timestamp=timestamp,
                response_time_ms=response_time_ms,
                error_message=str(e),
                success=False,
                health_status=HealthStatus.UNHEALTHY
            )
            
            self.stats.update_stats(result)
            return result
    
    def _evaluate_health(self, status_code: int, response_time_ms: float, response_body: str) -> HealthStatus:
        """Evaluate health status based on response"""
        
        # Check status code
        if status_code not in self.config.expected_status_codes:
            return HealthStatus.UNHEALTHY
        
        # Check response time SLA
        if (self.config.sla_response_time_ms and 
            response_time_ms > self.config.sla_response_time_ms):
            return HealthStatus.DEGRADED
        
        # Check expected response time threshold
        if (self.config.expected_response_time_ms and 
            response_time_ms > self.config.expected_response_time_ms):
            return HealthStatus.DEGRADED
        
        # Check response content
        if self.config.response_contains:
            if self.config.response_contains not in response_body:
                return HealthStatus.UNHEALTHY
        
        if self.config.response_not_contains:
            if self.config.response_not_contains in response_body:
                return HealthStatus.UNHEALTHY
        
        return HealthStatus.HEALTHY
    
    async def start_monitoring(self, callback=None):
        """
        Start continuous monitoring
        
        Args:
            callback: Optional callback function to receive check results
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._task = asyncio.create_task(self._monitor_loop(callback))
    
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        self._monitoring = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _monitor_loop(self, callback=None):
        """Main monitoring loop"""
        try:
            while self._monitoring:
                result = await self.check_health()
                
                if callback:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(result)
                        else:
                            callback(result)
                    except Exception as e:
                        print(f"Error in callback: {e}")
                
                await asyncio.sleep(self.config.check_interval_seconds)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in monitoring loop for {self.config.id}: {e}")
        finally:
            self._monitoring = False