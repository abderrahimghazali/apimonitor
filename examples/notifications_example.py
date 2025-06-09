"""
Notification examples for ApiMonitor
"""

import asyncio
import json
from apimonitor import ApiMonitor
from apimonitor.config import MonitorConfig
from apimonitor.models import EndpointConfig, NotificationConfig, NotificationType


async def example_console_notifications():
    """Example: Console notifications"""
    print("=== Console Notifications Example ===")
    
    config = MonitorConfig()
    
    # Add test endpoints (some will fail)
    config.add_endpoint(EndpointConfig(
        id="healthy_endpoint",
        url="https://httpbin.org/status/200",
        check_interval_seconds=60
    ))
    
    config.add_endpoint(EndpointConfig(
        id="unhealthy_endpoint", 
        url="https://httpbin.org/status/500",
        check_interval_seconds=60
    ))
    
    # Add console notification
    config.add_notification("console", NotificationConfig(
        type=NotificationType.CONSOLE,
        enabled=True,
        on_failure=True,
        on_recovery=True,
        on_degraded=True
    ))
    
    # Create monitor and check endpoints
    monitor = ApiMonitor(config)
    
    print("Checking endpoints with console notifications...")
    results = await monitor.check_all_endpoints()
    
    print(f"\nChecked {len(results)} endpoints")
    await monitor.close_sessions()


def example_slack_config():
    """Example: Slack notification configuration"""
    print("\n=== Slack Configuration Example ===")
    
    slack_config = {
        "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    }
    
    notification = NotificationConfig(
        type=NotificationType.SLACK,
        enabled=True,
        config=slack_config,
        on_failure=True,
        on_recovery=True,
        on_degraded=False,  # Don't alert on degraded performance
        max_notifications_per_hour=10,
        cooldown_minutes=5
    )
    
    print("Slack notification configuration:")
    print(f"  Type: {notification.type.value}")
    print(f"  Enabled: {notification.enabled}")
    print(f"  On Failure: {notification.on_failure}")
    print(f"  On Recovery: {notification.on_recovery}")
    print(f"  Max notifications/hour: {notification.max_notifications_per_hour}")
    print(f"  Cooldown: {notification.cooldown_minutes} minutes")


def example_discord_config():
    """Example: Discord notification configuration"""
    print("\n=== Discord Configuration Example ===")
    
    discord_config = {
        "webhook_url": "https://discord.com/api/webhooks/YOUR_DISCORD_WEBHOOK"
    }
    
    notification = NotificationConfig(
        type=NotificationType.DISCORD,
        enabled=True,
        config=discord_config,
        on_failure=True,
        on_recovery=True,
        max_notifications_per_hour=15,
        cooldown_minutes=3
    )
    
    print("Discord notification configuration:")
    print(f"  Webhook URL: {notification.config['webhook_url']}")
    print(f"  Rate limit: {notification.max_notifications_per_hour}/hour")


def example_email_config():
    """Example: Email notification configuration"""
    print("\n=== Email Configuration Example ===")
    
    email_config = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "alerts@yourcompany.com",
        "password": "your-app-password",  # Use app password for Gmail
        "from_email": "apimonitor@yourcompany.com",
        "to_emails": [
            "admin@yourcompany.com",
            "ops@yourcompany.com"
        ],
        "use_tls": True
    }
    
    notification = NotificationConfig(
        type=NotificationType.EMAIL,
        enabled=True,
        config=email_config,
        on_failure=True,
        on_recovery=True,
        max_notifications_per_hour=5,  # Lower rate for email
        cooldown_minutes=10
    )
    
    print("Email notification configuration:")
    print(f"  SMTP Host: {notification.config['smtp_host']}")
    print(f"  From: {notification.config['from_email']}")
    print(f"  To: {', '.join(notification.config['to_emails'])}")


def example_webhook_config():
    """Example: Webhook notification configuration"""
    print("\n=== Webhook Configuration Example ===")
    
    webhook_config = {
        "url": "https://your-webhook-service.com/alerts",
        "headers": {
            "Authorization": "Bearer your-webhook-token",
            "Content-Type": "application/json"
        }
    }
    
    notification = NotificationConfig(
        type=NotificationType.WEBHOOK,
        enabled=True,
        config=webhook_config,
        on_failure=True,
        on_recovery=True,
        max_notifications_per_hour=100  # Higher rate for webhooks
    )
    
    print("Webhook notification configuration:")
    print(f"  URL: {notification.config['url']}")
    print(f"  Headers: {notification.config['headers']}")


def example_comprehensive_config():
    """Example: Comprehensive configuration with multiple notifications"""
    print("\n=== Comprehensive Configuration Example ===")
    
    config = MonitorConfig()
    
    # Add multiple endpoints
    endpoints = [
        EndpointConfig(
            id="critical_api",
            url="https://api.yourcompany.com/health",
            check_interval_seconds=30,
            sla_uptime_percentage=99.9
        ),
        EndpointConfig(
            id="user_service",
            url="https://users.yourcompany.com/health",
            check_interval_seconds=60
        ),
        EndpointConfig(
            id="payment_service",
            url="https://payments.yourcompany.com/health",
            check_interval_seconds=30,
            sla_uptime_percentage=99.99  # Higher SLA for payments
        )
    ]
    
    for endpoint in endpoints:
        config.add_endpoint(endpoint)
    
    # Console notifications (always on)
    config.add_notification("console", NotificationConfig(
        type=NotificationType.CONSOLE,
        enabled=True,
        on_failure=True,
        on_recovery=True,
        on_degraded=True
    ))
    
    # Slack for general alerts
    config.add_notification("slack_general", NotificationConfig(
        type=NotificationType.SLACK,
        enabled=False,  # Disabled for example
        config={"webhook_url": "https://hooks.slack.com/services/GENERAL/WEBHOOK"},
        on_failure=True,
        on_recovery=True,
        max_notifications_per_hour=20
    ))
    
    # Slack for critical alerts
    config.add_notification("slack_critical", NotificationConfig(
        type=NotificationType.SLACK,
        enabled=False,  # Disabled for example
        config={"webhook_url": "https://hooks.slack.com/services/CRITICAL/WEBHOOK"},
        on_failure=True,
        on_recovery=False,  # Only failures for critical channel
        max_notifications_per_hour=50
    ))
    
    # Email for severe issues
    config.add_notification("email_alerts", NotificationConfig(
        type=NotificationType.EMAIL,
        enabled=False,  # Disabled for example
        config={
            "smtp_host": "smtp.company.com",
            "smtp_port": 587,
            "username": "alerts@yourcompany.com",
            "password": "password",
            "from_email": "apimonitor@yourcompany.com",
            "to_emails": ["oncall@yourcompany.com"]
        },
        on_failure=True,
        on_recovery=True,
        max_notifications_per_hour=3,  # Very limited for email
        cooldown_minutes=15
    ))
    
    # Save configuration
    config.to_file("comprehensive_config.yaml")
    print("Comprehensive configuration saved to: comprehensive_config.yaml")
    
    print(f"\nConfiguration summary:")
    print(f"  Endpoints: {len(config.endpoints)}")
    print(f"  Notification channels: {len(config.notifications)}")
    
    for name, notif in config.notifications.items():
        status = "enabled" if notif.enabled else "disabled"
        print(f"    {name}: {notif.type.value} ({status})")


async def main():
    """Run notification examples"""
    print("ApiMonitor Notification Examples")
    print("=" * 50)
    
    await example_console_notifications()
    example_slack_config()
    example_discord_config()
    example_email_config()
    example_webhook_config()
    example_comprehensive_config()
    
    print("\n" + "=" * 50)
    print("Notification examples completed!")
    print("\nTo use notifications:")
    print("1. Configure your notification channels in config.yaml")
    print("2. Set webhook URLs and credentials")
    print("3. Adjust rate limits and triggers as needed")
    print("4. Test with: apimonitor run --config-file config.yaml")


if __name__ == "__main__":
    asyncio.run(main())