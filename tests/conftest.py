"""
Test configuration and fixtures for ApiMonitor
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from apimonitor.config import MonitorConfig
from apimonitor.models import EndpointConfig, NotificationConfig, NotificationType
from apimonitor.monitor import ApiMonitor
from apimonitor.endpoint import Endpoint


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_endpoint_config():
    """Sample endpoint configuration for testing"""
    return EndpointConfig(
        id="test_endpoint",
        url="https://httpbin.org/status/200",
        check_interval_seconds=60,
        timeout_seconds=5,
        expected_status_codes=[200]
    )


@pytest.fixture
def sample_notification_config():
    """Sample notification configuration for testing"""
    return NotificationConfig(
        type=NotificationType.CONSOLE,
        enabled=True,
        on_failure=True,
        on_recovery=True
    )


@pytest.fixture
def sample_monitor_config(sample_endpoint_config, sample_notification_config):
    """Sample monitor configuration for testing"""
    config = MonitorConfig()
    config.endpoints = [sample_endpoint_config]
    config.notifications = {"console": sample_notification_config}
    return config


@pytest.fixture
def api_monitor(sample_monitor_config):
    """ApiMonitor instance for testing"""
    return ApiMonitor(sample_monitor_config)


@pytest.fixture
def config_file(temp_dir, sample_monitor_config):
    """Create a temporary config file"""
    config_path = Path(temp_dir) / "test_config.yaml"
    sample_monitor_config.to_file(config_path)
    return str(config_path)