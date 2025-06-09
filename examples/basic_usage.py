"""
Basic usage examples for ApiMonitor
"""

import asyncio
from apimonitor import ApiMonitor, quick_check
from apimonitor.config import MonitorConfig
from apimonitor.models import EndpointConfig, NotificationConfig, NotificationType


async def example_quick_check():
    """Example: Quick health check"""
    print("=== Quick Health Check ===")
    
    # Check a single endpoint
    result = await quick_check("https://httpbin.org/status/200")
    
    print(f"URL: https://httpbin.org/status/200")
    print(f"Status: {result.health_status.value}")
    print(f"Response Code: {result.status_code}")
    print(f"Response Time: {result.response_time_ms:.1f}ms")
    print(f"Success: {result.success}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")


async def example_basic_monitoring():
    """Example: Basic continuous monitoring"""
    print("\n=== Basic Monitoring ===")
    
    # Create monitor
    monitor = ApiMonitor()
    
    # Add endpoints
    monitor.add_endpoint("https://httpbin.org/status/200", "httpbin_200")
    monitor.add_endpoint("https://httpbin.org/status/500", "httpbin_500")
    monitor.add_endpoint("https://httpbin.org/delay/1", "httpbin_slow")
    
    # Check all endpoints once
    print("Checking all endpoints...")
    results = await monitor.check_all_endpoints()
    
    for result in results:
        status_symbol = "✓" if result.success else "✗"
        print(f"{status_symbol} {result.endpoint_id}: {result.health_status.value} "
              f"({result.response_time_ms:.1f}ms)" if result.response_time_ms else "")
    
    # Show statistics
    print("\nEndpoint Statistics:")
    for endpoint_id, stats in monitor.get_all_stats().items():
        print(f"  {endpoint_id}:")
        print(f"    Total checks: {stats.total_checks}")
        print(f"    Successful: {stats.successful_checks}")
        print(f"    Failed: {stats.failed_checks}")
        print(f"    Uptime: {stats.uptime_percentage:.1f}%")
        if stats.successful_checks > 0:
            print(f"    Avg response time: {stats.average_response_time:.1f}ms")
    
    await monitor.close_sessions()


async def example_config_file_monitoring():
    """Example: Monitoring with configuration file"""
    print("\n=== Configuration File Monitoring ===")
    
    # Create configuration programmatically
    config = MonitorConfig()
    
    # Add endpoints
    endpoints = [
        EndpointConfig(
            id="google",
            url="https://www.google.com",
            check_interval_seconds=60,
            timeout_seconds=5,
            expected_status_codes=[200]
        ),
        EndpointConfig(
            id="httpbin_json",
            url="https://httpbin.org/json",
            check_interval_seconds=120,
            timeout_seconds=10,
            response_contains="slideshow"
        )
    ]
    
    for endpoint in endpoints:
        config.add_endpoint(endpoint)
    
    # Add console notification
    config.add_notification("console", NotificationConfig(
        type=NotificationType.CONSOLE,
        enabled=True,
        on_failure=True,
        on_recovery=True
    ))
    
    # Create monitor with config
    monitor = ApiMonitor(config)
    
    print(f"Monitoring {len(config.endpoints)} endpoints...")
    
    # Check endpoints
    results = await monitor.check_all_endpoints()
    
    for result in results:
        print(f"Checked {result.endpoint_id}: {result.health_status.value}")
    
    # Show health summary
    summary = monitor.get_health_summary()
    print(f"\nOverall Status: {summary['status']}")
    print(f"Healthy endpoints: {summary['healthy']}/{summary['endpoints']}")
    
    await monitor.close_sessions()


async def example_advanced_endpoint_config():
    """Example: Advanced endpoint configuration"""
    print("\n=== Advanced Endpoint Configuration ===")
    
    monitor = ApiMonitor()
    
    # Add endpoint with custom headers and POST method
    monitor.add_endpoint(
        url="https://httpbin.org/post",
        endpoint_id="httpbin_post",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ApiMonitor/1.0"
        },
        timeout_seconds=15,
        expected_status_codes=[200],
        max_retries=3
    )
    
    # Add endpoint with response time SLA
    monitor.add_endpoint(
        url="https://httpbin.org/delay/2",
        endpoint_id="sla_test",
        expected_response_time_ms=1500,  # Expect under 1.5 seconds
        sla_response_time_ms=3000,       # SLA: under 3 seconds
        timeout_seconds=10
    )
    
    # Check endpoints
    results = await monitor.check_all_endpoints()
    
    for result in results:
        print(f"{result.endpoint_id}:")
        print(f"  Status: {result.health_status.value}")
        print(f"  Response Time: {result.response_time_ms:.1f}ms" if result.response_time_ms else "")
        print(f"  Status Code: {result.status_code}")
        
        if result.health_status.value == "degraded":
            print("  ⚠️  Performance degraded (slow response)")
        elif result.health_status.value == "unhealthy":
            print("  ❌ Endpoint unhealthy")
        else:
            print("  ✅ Endpoint healthy")
    
    await monitor.close_sessions()


async def example_error_handling():
    """Example: Error handling and edge cases"""
    print("\n=== Error Handling Examples ===")
    
    monitor = ApiMonitor()
    
    # Add endpoints that will fail in different ways
    monitor.add_endpoint("https://nonexistent-domain-12345.com", "invalid_domain")
    monitor.add_endpoint("https://httpbin.org/status/404", "not_found")
    monitor.add_endpoint("https://httpbin.org/delay/15", "timeout_test", timeout_seconds=2)
    
    results = await monitor.check_all_endpoints()
    
    for result in results:
        print(f"\n{result.endpoint_id}:")
        print(f"  Success: {result.success}")
        print(f"  Health Status: {result.health_status.value}")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")
        
        if result.status_code:
            print(f"  Status Code: {result.status_code}")
        
        if result.response_time_ms:
            print(f"  Response Time: {result.response_time_ms:.1f}ms")
    
    await monitor.close_sessions()


def example_save_config():
    """Example: Save configuration to file"""
    print("\n=== Save Configuration ===")
    
    # Create configuration
    config = MonitorConfig.create_example_config()
    
    # Save as YAML
    config.to_file("example_config.yaml")
    print("Configuration saved to: example_config.yaml")
    
    # Save as JSON
    config.to_file("example_config.json")
    print("Configuration saved to: example_config.json")
    
    # Load and verify
    loaded_config = MonitorConfig.from_file("example_config.yaml")
    print(f"Loaded config with {len(loaded_config.endpoints)} endpoints")


async def main():
    """Run all examples"""
    print("ApiMonitor Usage Examples")
    print("=" * 50)
    
    await example_quick_check()
    await example_basic_monitoring()
    await example_config_file_monitoring()
    await example_advanced_endpoint_config()
    await example_error_handling()
    example_save_config()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNext steps:")
    print("1. Create your own config file: apimonitor init")
    print("2. Start monitoring: apimonitor run --config-file config.yaml")
    print("3. Check the documentation for more advanced features")


if __name__ == "__main__":
    asyncio.run(main())