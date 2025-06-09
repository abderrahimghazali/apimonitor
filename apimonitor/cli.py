"""
Command Line Interface for ApiMonitor
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Optional, List

import click
import yaml
from tabulate import tabulate
from colorama import init as colorama_init, Fore, Style

from . import __version__
from .monitor import ApiMonitor, quick_check, create_example_config
from .config import MonitorConfig, load_config_from_env
from .models import HealthStatus, HttpMethod, NotificationType
from .exceptions import ApiMonitorError, ConfigurationError

# Initialize colorama for Windows compatibility
colorama_init()


def get_status_color(status: HealthStatus) -> str:
    """Get color for health status"""
    colors = {
        HealthStatus.HEALTHY: Fore.GREEN,
        HealthStatus.DEGRADED: Fore.YELLOW,
        HealthStatus.UNHEALTHY: Fore.RED,
        HealthStatus.UNKNOWN: Fore.MAGENTA
    }
    return colors.get(status, Fore.WHITE)


def print_status(message: str, status: HealthStatus = HealthStatus.UNKNOWN):
    """Print colored status message"""
    color = get_status_color(status)
    click.echo(f"{color}{message}{Style.RESET_ALL}")


@click.group()
@click.version_option(__version__)
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def main(ctx, config, verbose):
    """
    ApiMonitor - API Health Monitoring Tool
    
    Monitor your APIs, track response times, and get alerts when things go wrong.
    """
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['verbose'] = verbose


@main.command()
@click.argument('urls', nargs=-1, required=False)
@click.option('--config-file', '-c', help='Configuration file to use')
@click.option('--interval', '-i', default=300, help='Check interval in seconds', type=int)
@click.option('--timeout', '-t', default=10, help='Request timeout in seconds', type=float)
@click.option('--slack-webhook', help='Slack webhook URL for notifications')
@click.option('--discord-webhook', help='Discord webhook URL for notifications')
@click.option('--email-config', help='Email configuration (JSON string)')
@click.option('--log-level', default='INFO', help='Log level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--dashboard', is_flag=True, help='Enable web dashboard')
@click.option('--dashboard-port', default=8080, help='Dashboard port', type=int)
@click.option('--background', '-b', is_flag=True, help='Run in background')
@click.pass_context
def run(ctx, urls, config_file, interval, timeout, slack_webhook, discord_webhook, 
        email_config, log_level, dashboard, dashboard_port, background):
    """
    Start monitoring APIs
    
    Examples:
    
    \b
    # Monitor from config file
    apimonitor run --config-file config.yaml
    
    \b
    # Monitor specific URLs
    apimonitor run https://api.example.com/health https://api2.example.com/status
    
    \b
    # Monitor with Slack notifications
    apimonitor run https://api.example.com/health --slack-webhook WEBHOOK_URL
    
    \b
    # Monitor with dashboard
    apimonitor run --config-file config.yaml --dashboard --dashboard-port 8080
    """
    
    async def run_monitoring():
        try:
            # Load configuration
            if config_file:
                config = MonitorConfig.from_file(config_file)
            elif ctx.obj.get('config_file'):
                config = MonitorConfig.from_file(ctx.obj['config_file'])
            else:
                config = load_config_from_env()
            
            # Override config with CLI options
            config.log_level = log_level
            config.dashboard_enabled = dashboard
            config.dashboard_port = dashboard_port
            
            # Add URLs from command line
            if urls:
                for i, url in enumerate(urls):
                    endpoint_id = f"cli_endpoint_{i+1}"
                    config.add_endpoint({
                        'id': endpoint_id,
                        'url': url,
                        'check_interval_seconds': interval,
                        'timeout_seconds': timeout
                    })
            
            # Add notification channels from CLI
            if slack_webhook:
                config.add_notification('cli_slack', {
                    'type': NotificationType.SLACK,
                    'enabled': True,
                    'config': {'webhook_url': slack_webhook},
                    'on_failure': True,
                    'on_recovery': True
                })
            
            if discord_webhook:
                config.add_notification('cli_discord', {
                    'type': NotificationType.DISCORD,
                    'enabled': True,
                    'config': {'webhook_url': discord_webhook},
                    'on_failure': True,
                    'on_recovery': True
                })
            
            if email_config:
                try:
                    email_conf = json.loads(email_config)
                    config.add_notification('cli_email', {
                        'type': NotificationType.EMAIL,
                        'enabled': True,
                        'config': email_conf,
                        'on_failure': True,
                        'on_recovery': True
                    })
                except json.JSONDecodeError:
                    click.echo("Error: Invalid email configuration JSON", err=True)
                    return
            
            if not config.endpoints:
                click.echo("Error: No endpoints configured. Use --config-file or provide URLs", err=True)
                return
            
            # Start monitoring
            monitor = ApiMonitor(config)
            
            click.echo(f"Starting ApiMonitor v{__version__}")
            click.echo(f"Monitoring {len(config.endpoints)} endpoint(s)")
            
            if dashboard:
                click.echo(f"Dashboard available at: http://localhost:{dashboard_port}")
            
            # Start dashboard if enabled
            dashboard_task = None
            if dashboard:
                dashboard_task = asyncio.create_task(start_dashboard(monitor, dashboard_port))
            
            try:
                await monitor.start(background=background)
                
                if not background:
                    # Keep running until interrupted
                    while True:
                        await asyncio.sleep(1)
                        
            except KeyboardInterrupt:
                click.echo("\nShutting down...")
                await monitor.stop()
                
                if dashboard_task:
                    dashboard_task.cancel()
                    
        except ConfigurationError as e:
            click.echo(f"Configuration error: {e}", err=True)
            sys.exit(1)
        except ApiMonitorError as e:
            click.echo(f"ApiMonitor error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            if ctx.obj.get('verbose'):
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    # Run the async function
    asyncio.run(run_monitoring())


@main.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--timeout', '-t', default=10, help='Request timeout in seconds', type=float)
@click.option('--method', '-m', default='GET', help='HTTP method', 
              type=click.Choice(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH']))
@click.option('--headers', '-H', multiple=True, help='HTTP headers (key:value)')
@click.option('--expected-status', multiple=True, type=int, help='Expected status codes')
@click.option('--json-output', '-j', is_flag=True, help='Output results as JSON')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode (only show summary)')
@click.pass_context
def check(ctx, urls, timeout, method, headers, expected_status, json_output, quiet):
    """
    Check API endpoints once
    
    Examples:
    
    \b
    # Check single endpoint
    apimonitor check https://api.example.com/health
    
    \b
    # Check multiple endpoints
    apimonitor check https://api1.com/health https://api2.com/health
    
    \b
    # Check with custom headers and method
    apimonitor check https://api.example.com/data --method POST -H "Authorization:Bearer token"
    
    \b
    # Check with JSON output
    apimonitor check https://api.example.com/health --json-output
    """
    
    async def run_checks():
        results = []
        
        # Parse headers
        header_dict = {}
        for header in headers:
            if ':' in header:
                key, value = header.split(':', 1)
                header_dict[key.strip()] = value.strip()
        
        # Expected status codes
        expected_codes = list(expected_status) if expected_status else [200]
        
        for url in urls:
            if not quiet:
                click.echo(f"Checking {url}...")
            
            try:
                # Create endpoint config
                from .models import EndpointConfig
                config = EndpointConfig(
                    id=f"check_{url}",
                    url=url,
                    method=HttpMethod(method),
                    timeout_seconds=timeout,
                    headers=header_dict,
                    expected_status_codes=expected_codes
                )
                
                # Perform check
                from .endpoint import Endpoint
                endpoint = Endpoint(config)
                
                try:
                    await endpoint.start_session()
                    result = await endpoint.check_health()
                    results.append(result)
                    
                    if not quiet and not json_output:
                        status_color = get_status_color(result.health_status)
                        status_text = result.health_status.value.upper()
                        
                        click.echo(f"  {status_color}{status_text}{Style.RESET_ALL} - "
                                 f"{result.status_code or 'N/A'} - "
                                 f"{result.response_time_ms:.1f}ms" if result.response_time_ms else "N/A")
                        
                        if result.error_message:
                            click.echo(f"  Error: {result.error_message}")
                            
                finally:
                    await endpoint.close_session()
                    
            except Exception as e:
                if not quiet:
                    click.echo(f"  {Fore.RED}ERROR{Style.RESET_ALL} - {e}")
                    
                # Create error result
                from .models import CheckResult
                from datetime import datetime
                
                error_result = CheckResult(
                    endpoint_id=f"check_{url}",
                    timestamp=datetime.now(),
                    error_message=str(e),
                    success=False,
                    health_status=HealthStatus.UNHEALTHY
                )
                results.append(error_result)
        
        # Output results
        if json_output:
            output = [result.dict() for result in results]
            click.echo(json.dumps(output, indent=2, default=str))
        else:
            # Summary table
            if not quiet:
                click.echo("\nSummary:")
            
            table_data = []
            for result in results:
                status_icon = {
                    HealthStatus.HEALTHY: "✓",
                    HealthStatus.DEGRADED: "⚠",
                    HealthStatus.UNHEALTHY: "✗",
                    HealthStatus.UNKNOWN: "?"
                }.get(result.health_status, "?")
                
                table_data.append([
                    status_icon,
                    result.endpoint_id.replace("check_", ""),
                    result.health_status.value.upper(),
                    result.status_code or "N/A",
                    f"{result.response_time_ms:.1f}ms" if result.response_time_ms else "N/A",
                    result.error_message or ""
                ])
            
            headers = ["Status", "URL", "Health", "Code", "Time", "Error"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Overall summary
            healthy = sum(1 for r in results if r.health_status == HealthStatus.HEALTHY)
            total = len(results)
            
            if healthy == total:
                print_status(f"\n✓ All {total} endpoint(s) are healthy", HealthStatus.HEALTHY)
            else:
                unhealthy = total - healthy
                print_status(f"\n✗ {unhealthy}/{total} endpoint(s) have issues", HealthStatus.UNHEALTHY)
    
    asyncio.run(run_checks())


@main.command()
@click.option('--output', '-o', default='apimonitor_config.yaml', help='Output file path')
@click.option('--format', '-f', default='yaml', type=click.Choice(['yaml', 'json']), help='Output format')
def init(output, format):
    """
    Create example configuration file
    
    Examples:
    
    \b
    # Create YAML config
    apimonitor init --output config.yaml
    
    \b
    # Create JSON config
    apimonitor init --output config.json --format json
    """
    
    try:
        if format == 'json' and not output.endswith('.json'):
            output = output.replace('.yaml', '.json').replace('.yml', '.json')
        
        config = MonitorConfig.create_example_config()
        config.to_file(output)
        
        click.echo(f"✓ Example configuration created: {output}")
        click.echo(f"Edit the file to configure your endpoints and notifications.")
        click.echo(f"Then run: apimonitor run --config-file {output}")
        
    except Exception as e:
        click.echo(f"Error creating configuration: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config-file', '-c', required=True, help='Configuration file to validate')
def validate(config_file):
    """
    Validate configuration file
    
    Examples:
    
    \b
    # Validate config file
    apimonitor validate --config-file config.yaml
    """
    
    try:
        config = MonitorConfig.from_file(config_file)
        
        click.echo(f"✓ Configuration file is valid: {config_file}")
        click.echo(f"  - {len(config.endpoints)} endpoint(s) configured")
        click.echo(f"  - {len(config.notifications)} notification channel(s) configured")
        
        # Show endpoints
        if config.endpoints:
            click.echo("\nEndpoints:")
            for ep in config.endpoints:
                click.echo(f"  - {ep.id}: {ep.url} (every {ep.check_interval_seconds}s)")
        
        # Show notifications
        if config.notifications:
            click.echo("\nNotification Channels:")
            for name, notif in config.notifications.items():
                status = "enabled" if notif.enabled else "disabled"
                click.echo(f"  - {name}: {notif.type.value} ({status})")
                
    except ConfigurationError as e:
        click.echo(f"✗ Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error validating configuration: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config-file', '-c', help='Configuration file to use')
@click.option('--endpoint', '-e', help='Show stats for specific endpoint')
@click.option('--hours', default=24, help='Hours of history to show', type=int)
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
def stats(config_file, endpoint, hours, json_output):
    """
    Show monitoring statistics
    
    Examples:
    
    \b
    # Show all stats
    apimonitor stats --config-file config.yaml
    
    \b
    # Show stats for specific endpoint
    apimonitor stats --config-file config.yaml --endpoint api_health
    
    \b
    # Show last 12 hours
    apimonitor stats --config-file config.yaml --hours 12
    """
    
    async def show_stats():
        try:
            # Load config and create monitor (without starting)
            if config_file:
                config = MonitorConfig.from_file(config_file)
            else:
                config = load_config_from_env()
            
            monitor = ApiMonitor(config)
            
            # Get stats (this would normally be loaded from persistent storage)
            all_stats = monitor.get_all_stats()
            
            if json_output:
                if endpoint:
                    stats_data = all_stats.get(endpoint)
                    if stats_data:
                        click.echo(json.dumps(stats_data.dict(), indent=2, default=str))
                    else:
                        click.echo(f"Endpoint '{endpoint}' not found", err=True)
                        sys.exit(1)
                else:
                    output = {k: v.dict() for k, v in all_stats.items()}
                    click.echo(json.dumps(output, indent=2, default=str))
                return
            
            if endpoint:
                # Show stats for specific endpoint
                if endpoint not in all_stats:
                    click.echo(f"Endpoint '{endpoint}' not found", err=True)
                    sys.exit(1)
                
                stats_data = all_stats[endpoint]
                click.echo(f"\nStats for {endpoint}:")
                click.echo(f"  Status: {get_status_color(stats_data.current_status)}{stats_data.current_status.value.upper()}{Style.RESET_ALL}")
                click.echo(f"  Uptime: {stats_data.uptime_percentage:.2f}%")
                click.echo(f"  Total Checks: {stats_data.total_checks}")
                click.echo(f"  Successful: {stats_data.successful_checks}")
                click.echo(f"  Failed: {stats_data.failed_checks}")
                
                if stats_data.successful_checks > 0:
                    click.echo(f"  Avg Response Time: {stats_data.average_response_time:.1f}ms")
                    click.echo(f"  Min Response Time: {stats_data.min_response_time:.1f}ms")
                    click.echo(f"  Max Response Time: {stats_data.max_response_time:.1f}ms")
                
                if stats_data.last_check:
                    click.echo(f"  Last Check: {stats_data.last_check.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # Show summary for all endpoints
                if not all_stats:
                    click.echo("No statistics available")
                    return
                
                click.echo(f"\nMonitoring Statistics ({hours} hours):")
                
                table_data = []
                for endpoint_id, stats_data in all_stats.items():
                    status_icon = {
                        HealthStatus.HEALTHY: "✓",
                        HealthStatus.DEGRADED: "⚠",
                        HealthStatus.UNHEALTHY: "✗",
                        HealthStatus.UNKNOWN: "?"
                    }.get(stats_data.current_status, "?")
                    
                    table_data.append([
                        status_icon,
                        endpoint_id,
                        f"{stats_data.uptime_percentage:.1f}%",
                        stats_data.total_checks,
                        f"{stats_data.average_response_time:.0f}ms" if stats_data.successful_checks > 0 else "N/A",
                        stats_data.last_check.strftime('%H:%M:%S') if stats_data.last_check else "Never"
                    ])
                
                headers = ["Status", "Endpoint", "Uptime", "Checks", "Avg Time", "Last Check"]
                click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
                
        except Exception as e:
            click.echo(f"Error showing stats: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(show_stats())


async def start_dashboard(monitor: ApiMonitor, port: int):
    """Start the web dashboard"""
    try:
        # This would import and start the dashboard
        # For now, just a placeholder
        click.echo(f"Dashboard would start on port {port}")
        # await dashboard.start(monitor, port)
    except ImportError:
        click.echo("Dashboard dependencies not installed. Run: pip install apimonitor[dashboard]")
    except Exception as e:
        click.echo(f"Error starting dashboard: {e}")


if __name__ == '__main__':
    main()