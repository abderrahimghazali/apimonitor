# 🔍 ApiMonitor

A fast, flexible, and powerful API health monitoring tool for Python. Monitor your APIs, track response times, get alerts when things go wrong, and ensure your services stay online.

## ✨ Features

- 🚀 **Fast Async Monitoring**: Built with aiohttp for high-performance concurrent checks
- 📊 **Comprehensive Metrics**: Response times, status codes, uptime percentages, SLA tracking
- 🚨 **Multiple Alert Channels**: Slack, Discord, Email, Webhooks, Console notifications
- 🎛️ **Flexible Configuration**: YAML/JSON config files or programmatic setup
- 📈 **Built-in Dashboard**: Web interface for real-time monitoring (optional)
- 🐳 **Docker Ready**: Easy deployment with Docker support
- 💻 **CLI & Python API**: Use from command line or integrate into your applications
- 🔧 **Highly Configurable**: Custom headers, request bodies, health checks, retry logic

## 🚀 Quick Start

### Installation

```bash
pip install apimonitor
```

### Command Line Usage

```bash
# Check endpoints once
apimonitor check https://api.example.com/health https://api2.example.com/status

# Monitor continuously
apimonitor run https://api.example.com/health --interval 60

# Monitor with Slack notifications
apimonitor run https://api.example.com/health --slack-webhook YOUR_WEBHOOK_URL

# Use configuration file
apimonitor init  # Create example config
apimonitor run --config-file apimonitor_config.yaml

# Start with dashboard
apimonitor run --config-file config.yaml --dashboard --dashboard-port 8080
```

### Python API

```python
from apimonitor import ApiMonitor

# Quick health check
from apimonitor import quick_check
result = await quick_check("https://api.example.com/health")
print(f"Status: {result.health_status}, Response time: {result.response_time_ms}ms")

# Continuous monitoring
monitor = ApiMonitor()
monitor.add_endpoint("https://api.example.com/health", "api_health")
monitor.add_notification_channel("slack", "slack", {
    "webhook_url": "YOUR_SLACK_WEBHOOK_URL"
})

# Start monitoring
await monitor.start()
```

## 📋 Configuration

### YAML Configuration Example

```yaml
# Basic settings
log_level: "INFO"
max_history_days: 30
dashboard_enabled: true
dashboard_port: 8080

# Endpoints to monitor
endpoints:
  - id: "api_health"
    url: "https://api.example.com/health"
    method: "GET"
    check_interval_seconds: 60
    timeout_seconds: 10
    expected_status_codes: [200]
    headers:
      Authorization: "Bearer your-token"
    
  - id: "api_users"
    url: "https://api.example.com/users"
    method: "GET"
    check_interval_seconds: 300
    timeout_seconds: 5
    expected_status_codes: [200, 201]
    sla_response_time_ms: 1000
    response_contains: "users"

# Notification channels
notifications:
  console:
    type: "console"
    enabled: true
    on_failure: true
    on_recovery: true
    
  slack:
    type: "slack"
    enabled: true
    config:
      webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    on_failure: true
    on_recovery: true
    max_notifications_per_hour: 10
    cooldown_minutes: 5
    
  email:
    type: "email"
    enabled: false
    config:
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      username: "your-email@gmail.com"
      password: "your-app-password"
      from_email: "monitoring@yourcompany.com"
      to_emails: ["admin@yourcompany.com", "ops@yourcompany.com"]
      use_tls: true
```

### Environment Variables

You can also configure ApiMonitor using environment variables:

```bash
export APIMONITOR_URL="https://api.example.com/health"
export APIMONITOR_INTERVAL=300
export APIMONITOR_TIMEOUT=10
export APIMONITOR_SLACK_WEBHOOK="https://hooks.slack.com/services/..."
export APIMONITOR_LOG_LEVEL="INFO"
export APIMONITOR_DASHBOARD=true

apimonitor run
```

## 🔧 Advanced Usage

### Custom Health Checks

```python
from apimonitor import ApiMonitor
from apimonitor.models import EndpointConfig, HttpMethod

# Advanced endpoint configuration
endpoint = EndpointConfig(
    id="api_advanced",
    url="https://api.example.com/data",
    method=HttpMethod.POST,
    headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
    body='{"query": "test"}',
    expected_status_codes=[200, 201],
    expected_response_time_ms=500,
    response_contains="success",
    response_not_contains="error",
    check_interval_seconds=120,
    max_retries=3,
    sla_uptime_percentage=99.9,
    sla_response_time_ms=1000
)

monitor = ApiMonitor()
monitor.config.add_endpoint(endpoint)
```

### Custom Notifications

```python
# Webhook notification
monitor.add_notification_channel("webhook", "webhook", {
    "url": "https://your-webhook.com/alerts",
    "headers": {"Authorization": "Bearer webhook-token"}
})

# Discord notification
monitor.add_notification_channel("discord", "discord", {
    "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK"
})

# Email notification
monitor.add_notification_channel("email", "email", {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "alerts@yourcompany.com",
    "password": "your-password",
    "from_email": "alerts@yourcompany.com",
    "to_emails": ["admin@yourcompany.com"]
})
```

### Monitoring with Context Manager

```python
async with ApiMonitor() as monitor:
    monitor.add_endpoint("https://api.example.com/health", "api_health")
    
    # Check once
    result = await monitor.check_endpoint("api_health")
    print(f"Health: {result.health_status}")
    
    # Get statistics
    stats = monitor.get_endpoint_stats("api_health")
    print(f"Uptime: {stats.uptime_percentage:.2f}%")
```

## 📊 Dashboard

ApiMonitor includes an optional web dashboard for real-time monitoring:

```bash
# Install dashboard dependencies
pip install apimonitor[dashboard]

# Start with dashboard
apimonitor run --config-file config.yaml --dashboard --dashboard-port 8080
```

Visit `http://localhost:8080` to see:
- Real-time endpoint status
- Response time graphs
- Uptime statistics  
- Recent alerts and events
- SLA compliance tracking

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY config.yaml .
COPY . .

CMD ["apimonitor", "run", "--config-file", "config.yaml"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  apimonitor:
    build: .
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    environment:
      - APIMONITOR_LOG_LEVEL=INFO
    restart: unless-stopped
```

## 📚 CLI Reference

### Commands

- `apimonitor run` - Start continuous monitoring
- `apimonitor check` - Check endpoints once
- `apimonitor init` - Create example configuration
- `apimonitor validate` - Validate configuration file
- `apimonitor stats` - Show monitoring statistics

### Global Options

- `--config`, `-c` - Configuration file path
- `--verbose`, `-v` - Verbose output
- `--version` - Show version

### Run Command Options

- `--config-file`, `-c` - Configuration file
- `--interval`, `-i` - Check interval in seconds
- `--timeout`, `-t` - Request timeout in seconds
- `--slack-webhook` - Slack webhook URL
- `--discord-webhook` - Discord webhook URL
- `--email-config` - Email configuration (JSON)
- `--dashboard` - Enable web dashboard
- `--dashboard-port` - Dashboard port
- `--background`, `-b` - Run in background

### Check Command Options

- `--timeout`, `-t` - Request timeout in seconds
- `--method`, `-m` - HTTP method
- `--headers`, `-H` - HTTP headers (key:value)
- `--expected-status` - Expected status codes
- `--json-output`, `-j` - Output as JSON
- `--quiet`, `-q` - Quiet mode

## 🧪 Testing

```bash
# Install test dependencies
pip install apimonitor[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=apimonitor --cov-report=html
```

## 🔄 Integration Examples

### CI/CD Pipeline Health Check

```yaml
# GitHub Actions example
- name: Check API Health
  run: |
    pip install apimonitor
    apimonitor check https://api.staging.example.com/health --expected-status 200
```

### Kubernetes Health Check

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: api-health-check
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: apimonitor
            image: your-registry/apimonitor:latest
            command: ["apimonitor", "check", "https://api.example.com/health"]
          restartPolicy: OnFailure
```

### Serverless Monitoring (AWS Lambda)

```python
import json
import asyncio
from apimonitor import quick_check

def lambda_handler(event, context):
    async def check_apis():
        urls = ["https://api1.example.com/health", "https://api2.example.com/health"]
        results = []
        
        for url in urls:
            result = await quick_check(url)
            results.append({
                "url": url,
                "status": result.health_status.value,
                "response_time": result.response_time_ms,
                "success": result.success
            })
        
        return results
    
    results = asyncio.run(check_apis())
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/abderrahimghazali/apimonitor.git
cd apimonitor

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black apimonitor/ tests/
isort apimonitor/ tests/

# Lint code
flake8 apimonitor/ tests/
```

## 🐛 Troubleshooting

### Common Issues

**1. SSL Certificate Errors**
```python
# Disable SSL verification (not recommended for production)
endpoint_config = EndpointConfig(
    id="test",
    url="https://self-signed-cert-site.com",
    # Add custom session configuration in future versions
)
```

**2. Timeout Issues**
```yaml
endpoints:
  - id: "slow_api"
    url: "https://slow-api.example.com"
    timeout_seconds: 30  # Increase timeout
    max_retries: 5       # Increase retries
```

**3. Rate Limiting**
```yaml
endpoints:
  - id: "rate_limited_api"
    url: "https://api.example.com"
    check_interval_seconds: 600  # Check less frequently
```

**4. Memory Usage**
```yaml
# Limit history retention
max_history_days: 7
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [aiohttp](https://aiohttp.readthedocs.io/) for fast async HTTP requests
- Uses [pydantic](https://pydantic-docs.helpmanual.io/) for configuration validation
- CLI powered by [click](https://click.palletsprojects.com/)
- Dashboard built with [FastAPI](https://fastapi.tiangolo.com/) (optional)

---

**Need help?** 
- 📖 [Documentation](https://github.com/yourusername/apimonitor/wiki)
- 🐛 [Report Issues](https://github.com/yourusername/apimonitor/issues)
- 💬 [Discussions](https://github.com/yourusername/apimonitor/discussions)

---

# Example Configuration Files

## config/basic.yaml
```yaml
log_level: "INFO"
dashboard_enabled: false

endpoints:
  - id: "google"
    url: "https://www.google.com"
    check_interval_seconds: 300
    timeout_seconds: 10
    expected_status_codes: [200]

notifications:
  console:
    type: "console"
    enabled: true
    on_failure: true
    on_recovery: true
```

## config/advanced.yaml
```yaml
log_level: "INFO"
log_file: "logs/apimonitor.log"
max_history_days: 30
dashboard_enabled: true
dashboard_port: 8080

# Default settings for all endpoints
default_timeout: 10.0
default_interval: 300
default_retries: 3

endpoints:
  - id: "api_health"
    url: "https://api.example.com/health"
    method: "GET"
    check_interval_seconds: 60
    timeout_seconds: 5
    expected_status_codes: [200]
    expected_response_time_ms: 500
    headers:
      User-Agent: "ApiMonitor/1.0"
      Authorization: "Bearer token123"
    sla_uptime_percentage: 99.9
    sla_response_time_ms: 1000

  - id: "api_users_post"
    url: "https://api.example.com/users"
    method: "POST"
    check_interval_seconds: 300
    timeout_seconds: 10
    expected_status_codes: [200, 201]
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer token123"
    body: '{"test": true}'
    response_contains: "success"
    max_retries: 5
    retry_delay_seconds: 2.0

  - id: "slow_api"
    url: "https://httpbin.org/delay/3"
    check_interval_seconds: 600
    timeout_seconds: 15
    expected_status_codes: [200]
    expected_response_time_ms: 5000

notifications:
  console:
    type: "console"
    enabled: true
    on_failure: true
    on_recovery: true
    on_degraded: true

  slack_critical:
    type: "slack"
    enabled: true
    config:
      webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    on_failure: true
    on_recovery: true
    on_degraded: false
    max_notifications_per_hour: 20
    cooldown_minutes: 2

  discord_alerts:
    type: "discord"
    enabled: true
    config:
      webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK"
    on_failure: true
    on_recovery: true
    max_notifications_per_hour: 10
    cooldown_minutes: 5

  email_alerts:
    type: "email"
    enabled: false
    config:
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      username: "alerts@yourcompany.com"
      password: "your-app-password"
      from_email: "apimonitor@yourcompany.com"
      to_emails: 
        - "admin@yourcompany.com"
        - "ops@yourcompany.com"
      use_tls: true
    on_failure: true
    on_recovery: true
    max_notifications_per_hour: 5
    cooldown_minutes: 10

  webhook_integration:
    type: "webhook"
    enabled: false
    config:
      url: "https://your-webhook-service.com/alerts"
      headers:
        Authorization: "Bearer webhook-token"
        Content-Type: "application/json"
    on_failure: true
    on_recovery: true
    max_notifications_per_hour: 50
```

## config/microservices.yaml
```yaml
log_level: "INFO"
dashboard_enabled: true
dashboard_port: 8080

endpoints:
  # Frontend services
  - id: "web_frontend"
    url: "https://app.example.com/health"
    check_interval_seconds: 60
    timeout_seconds: 5
    expected_status_codes: [200]
    sla_uptime_percentage: 99.9

  # API Gateway
  - id: "api_gateway"
    url: "https://api.example.com/health"
    check_interval_seconds: 30
    timeout_seconds: 5
    expected_status_codes: [200]
    sla_uptime_percentage: 99.95

  # User service
  - id: "user_service"
    url: "https://users.example.com/health"
    check_interval_seconds: 120
    timeout_seconds: 10
    expected_status_codes: [200]
    headers:
      Authorization: "Bearer service-token"

  # Payment service (critical)
  - id: "payment_service"
    url: "https://payments.example.com/health"
    check_interval_seconds: 30
    timeout_seconds: 5
    expected_status_codes: [200]
    sla_uptime_percentage: 99.99
    sla_response_time_ms: 200

  # Email service
  - id: "email_service"
    url: "https://email.example.com/health"
    check_interval_seconds: 300
    timeout_seconds: 10
    expected_status_codes: [200]

  # Database health check
  - id: "database_proxy"
    url: "https://db-proxy.example.com/health"
    check_interval_seconds: 60
    timeout_seconds: 3
    expected_status_codes: [200]
    response_contains: "database_ok"

notifications:
  console:
    type: "console"
    enabled: true
    on_failure: true
    on_recovery: true

  slack_ops:
    type: "slack"
    enabled: true
    config:
      webhook_url: "https://hooks.slack.com/services/YOUR/OPS/WEBHOOK"
    on_failure: true
    on_recovery: true
    on_degraded: true
    max_notifications_per_hour: 30

  slack_critical:
    type: "slack"
    enabled: true
    config:
      webhook_url: "https://hooks.slack.com/services/YOUR/CRITICAL/WEBHOOK"
    on_failure: true
    on_recovery: false  # Only failures for critical channel
    max_notifications_per_hour: 50
```

## docker-compose.yaml
```yaml
version: '3.8'

services:
  apimonitor:
    build: .
    container_name: apimonitor
    volumes:
      - ./config/production.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8080:8080"
    environment:
      - APIMONITOR_LOG_LEVEL=INFO
      - APIMONITOR_CONFIG=/app/config.yaml
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Redis for shared state (future enhancement)
  redis:
    image: redis:7-alpine
    container_name: apimonitor-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

## Kubernetes Deployment

### k8s/configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apimonitor-config
data:
  config.yaml: |
    log_level: "INFO"
    dashboard_enabled: true
    dashboard_port: 8080
    
    endpoints:
      - id: "frontend"
        url: "http://frontend-service/health"
        check_interval_seconds: 60
        timeout_seconds: 5
        expected_status_codes: [200]
    
    notifications:
      console:
        type: "console"
        enabled: true
        on_failure: true
        on_recovery: true
```

### k8s/deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apimonitor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: apimonitor
  template:
    metadata:
      labels:
        app: apimonitor
    spec:
      containers:
      - name: apimonitor
        image: your-registry/apimonitor:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        env:
        - name: APIMONITOR_CONFIG
          value: "/app/config.yaml"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: apimonitor-config
```

### k8s/service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: apimonitor-service
spec:
  selector:
    app: apimonitor
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```