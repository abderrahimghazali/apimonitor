"""
Notification system for ApiMonitor
"""

import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
import aiohttp

from .models import CheckResult, NotificationConfig, NotificationType, HealthStatus
from .exceptions import NotificationError


class NotificationManager:
    """
    Manages notifications for API monitoring events
    """
    
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.notification_history: List[Dict] = []
        self.rate_limits: Dict[str, List[datetime]] = {}
    
    def add_channel(self, name: str, config: NotificationConfig):
        """Add a notification channel"""
        channel_class = self._get_channel_class(config.type)
        self.channels[name] = channel_class(config)
    
    def _get_channel_class(self, notification_type: NotificationType):
        """Get the appropriate channel class"""
        channel_map = {
            NotificationType.SLACK: SlackNotification,
            NotificationType.DISCORD: DiscordNotification,
            NotificationType.EMAIL: EmailNotification,
            NotificationType.WEBHOOK: WebhookNotification,
            NotificationType.CONSOLE: ConsoleNotification,
        }
        return channel_map.get(notification_type, ConsoleNotification)
    
    async def send_notification(self, result: CheckResult, message: str, channel_names: List[str] = None):
        """Send notification to specified channels"""
        
        if channel_names is None:
            channel_names = list(self.channels.keys())
        
        for channel_name in channel_names:
            if channel_name not in self.channels:
                continue
            
            channel = self.channels[channel_name]
            
            # Check if notification should be sent
            if not self._should_send_notification(channel, result):
                continue
            
            # Check rate limits
            if self._is_rate_limited(channel_name, channel.config):
                continue
            
            try:
                await channel.send(result, message)
                self._record_notification(channel_name, result, message)
            except Exception as e:
                print(f"Failed to send notification via {channel_name}: {e}")
    
    def _should_send_notification(self, channel: 'NotificationChannel', result: CheckResult) -> bool:
        """Check if notification should be sent based on configuration"""
        if not channel.config.enabled:
            return False
        
        if result.health_status == HealthStatus.UNHEALTHY and channel.config.on_failure:
            return True
        
        if result.health_status == HealthStatus.HEALTHY and channel.config.on_recovery:
            # Only send recovery notification if previous status was unhealthy
            # This would require tracking previous status
            return True
        
        if result.health_status == HealthStatus.DEGRADED and channel.config.on_degraded:
            return True
        
        return False
    
    def _is_rate_limited(self, channel_name: str, config: NotificationConfig) -> bool:
        """Check if channel is rate limited"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old notifications
        if channel_name not in self.rate_limits:
            self.rate_limits[channel_name] = []
        
        self.rate_limits[channel_name] = [
            ts for ts in self.rate_limits[channel_name] if ts > hour_ago
        ]
        
        # Check if rate limit exceeded
        if len(self.rate_limits[channel_name]) >= config.max_notifications_per_hour:
            return True
        
        # Check cooldown
        if self.rate_limits[channel_name]:
            last_notification = max(self.rate_limits[channel_name])
            cooldown = timedelta(minutes=config.cooldown_minutes)
            if now - last_notification < cooldown:
                return True
        
        return False
    
    def _record_notification(self, channel_name: str, result: CheckResult, message: str):
        """Record sent notification"""
        now = datetime.now()
        
        self.rate_limits.setdefault(channel_name, []).append(now)
        
        self.notification_history.append({
            'timestamp': now,
            'channel': channel_name,
            'endpoint_id': result.endpoint_id,
            'status': result.health_status,
            'message': message
        })
        
        # Keep only last 1000 notifications
        self.notification_history = self.notification_history[-1000:]


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
    
    async def send(self, result: CheckResult, message: str):
        """Send notification (to be implemented by subclasses)"""
        raise NotImplementedError


class SlackNotification(NotificationChannel):
    """Slack notification channel"""
    
    async def send(self, result: CheckResult, message: str):
        webhook_url = self.config.config.get('webhook_url')
        if not webhook_url:
            raise NotificationError("Slack webhook_url not configured")
        
        # Create Slack message
        color = {
            HealthStatus.HEALTHY: "good",
            HealthStatus.DEGRADED: "warning", 
            HealthStatus.UNHEALTHY: "danger",
            HealthStatus.UNKNOWN: "#808080"
        }.get(result.health_status, "#808080")
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"API Monitor Alert - {result.endpoint_id}",
                "text": message,
                "fields": [
                    {"title": "Status", "value": result.health_status.value.title(), "short": True},
                    {"title": "Response Time", "value": f"{result.response_time_ms:.1f}ms" if result.response_time_ms else "N/A", "short": True},
                    {"title": "Status Code", "value": str(result.status_code) if result.status_code else "N/A", "short": True},
                    {"title": "Timestamp", "value": result.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ],
                "ts": int(result.timestamp.timestamp())
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise NotificationError(f"Slack notification failed: {response.status}")


class DiscordNotification(NotificationChannel):
    """Discord notification channel"""
    
    async def send(self, result: CheckResult, message: str):
        webhook_url = self.config.config.get('webhook_url')
        if not webhook_url:
            raise NotificationError("Discord webhook_url not configured")
        
        # Create Discord embed
        color = {
            HealthStatus.HEALTHY: 0x00ff00,    # Green
            HealthStatus.DEGRADED: 0xffff00,   # Yellow
            HealthStatus.UNHEALTHY: 0xff0000,  # Red
            HealthStatus.UNKNOWN: 0x808080     # Gray
        }.get(result.health_status, 0x808080)
        
        embed = {
            "title": f"API Monitor Alert - {result.endpoint_id}",
            "description": message,
            "color": color,
            "timestamp": result.timestamp.isoformat(),
            "fields": [
                {"name": "Status", "value": result.health_status.value.title(), "inline": True},
                {"name": "Response Time", "value": f"{result.response_time_ms:.1f}ms" if result.response_time_ms else "N/A", "inline": True},
                {"name": "Status Code", "value": str(result.status_code) if result.status_code else "N/A", "inline": True}
            ]
        }
        
        payload = {"embeds": [embed]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 204]:
                    raise NotificationError(f"Discord notification failed: {response.status}")


class EmailNotification(NotificationChannel):
    """Email notification channel"""
    
    async def send(self, result: CheckResult, message: str):
        smtp_config = self.config.config
        required_keys = ['smtp_host', 'smtp_port', 'username', 'password', 'from_email', 'to_emails']
        
        for key in required_keys:
            if key not in smtp_config:
                raise NotificationError(f"Email {key} not configured")
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = ', '.join(smtp_config['to_emails'])
        msg['Subject'] = f"API Monitor Alert - {result.endpoint_id} - {result.health_status.value.title()}"
        
        # Email body
        body = f"""
API Monitor Alert

Endpoint: {result.endpoint_id}
Status: {result.health_status.value.title()}
Message: {message}
Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Details:
- Response Time: {result.response_time_ms:.1f}ms if result.response_time_ms else 'N/A'
- Status Code: {result.status_code or 'N/A'}
- Error: {result.error_message or 'None'}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (simplified, could use aiosmtplib for async)
        try:
            with smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
        except Exception as e:
            raise NotificationError(f"Failed to send email: {e}")


class WebhookNotification(NotificationChannel):
    """Generic webhook notification channel"""
    
    async def send(self, result: CheckResult, message: str):
        webhook_url = self.config.config.get('url')
        if not webhook_url:
            raise NotificationError("Webhook URL not configured")
        
        payload = {
            'endpoint_id': result.endpoint_id,
            'status': result.health_status.value,
            'message': message,
            'timestamp': result.timestamp.isoformat(),
            'response_time_ms': result.response_time_ms,
            'status_code': result.status_code,
            'error_message': result.error_message,
            'success': result.success
        }
        
        headers = self.config.config.get('headers', {})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, headers=headers) as response:
                if response.status not in [200, 201, 202, 204]:
                    raise NotificationError(f"Webhook notification failed: {response.status}")


class ConsoleNotification(NotificationChannel):
    """Console notification channel"""
    
    async def send(self, result: CheckResult, message: str):
        # Color output
        colors = {
            HealthStatus.HEALTHY: '\033[92m',    # Green
            HealthStatus.DEGRADED: '\033[93m',   # Yellow
            HealthStatus.UNHEALTHY: '\033[91m',  # Red
            HealthStatus.UNKNOWN: '\033[90m'     # Gray
        }
        reset = '\033[0m'
        
        color = colors.get(result.health_status, '')
        status = result.health_status.value.upper()
        
        print(f"{color}[{result.timestamp.strftime('%H:%M:%S')}] {status} - {result.endpoint_id}: {message}{reset}")
        
        if result.response_time_ms:
            print(f"  Response time: {result.response_time_ms:.1f}ms")
        
        if result.error_message:
            print(f"  Error: {result.error_message}")