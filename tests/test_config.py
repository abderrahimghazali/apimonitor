"""
Tests for configuration management
"""

import pytest
import json
import yaml
from pathlib import Path

from apimonitor.config import MonitorConfig, load_config_from_env
from apimonitor.models import EndpointConfig, NotificationConfig, NotificationType
from apimonitor.exceptions import ConfigurationError


class TestMonitorConfig:
    
    def test_default_config(self):
        """Test default configuration creation"""
        config = MonitorConfig()
        
        assert config.log_level == "INFO"
        assert config.max_history_days == 30
        assert config.dashboard_enabled == False
        assert len(config.endpoints) == 0
        assert len(config.notifications) == 0
    
    def test_add_endpoint(self):
        """Test adding endpoint to configuration"""
        config = MonitorConfig()
        endpoint = EndpointConfig(
            id="test",
            url="https://example.com"
        )
        
        config.add_endpoint(endpoint)
        
        assert len(config.endpoints) == 1
        assert config.endpoints[0].id == "test"
    
    def test_duplicate_endpoint_id(self):
        """Test adding endpoint with duplicate ID"""
        config = MonitorConfig()
        endpoint1 = EndpointConfig(id="test", url="https://example.com")
        endpoint2 = EndpointConfig(id="test", url="https://other.com")
        
        config.add_endpoint(endpoint1)
        
        with pytest.raises(ConfigurationError):
            config.add_endpoint(endpoint2)
    
    def test_get_endpoint(self):
        """Test getting endpoint by ID"""
        config = MonitorConfig()
        endpoint = EndpointConfig(id="test", url="https://example.com")
        config.add_endpoint(endpoint)
        
        found = config.get_endpoint("test")
        assert found is not None
        assert found.id == "test"
        
        not_found = config.get_endpoint("nonexistent")
        assert not_found is None
    
    def test_remove_endpoint(self):
        """Test removing endpoint"""
        config = MonitorConfig()
        endpoint = EndpointConfig(id="test", url="https://example.com")
        config.add_endpoint(endpoint)
        
        assert len(config.endpoints) == 1
        
        removed = config.remove_endpoint("test")
        assert removed == True
        assert len(config.endpoints) == 0
        
        not_removed = config.remove_endpoint("nonexistent")
        assert not_removed == False


class TestConfigFile:
    
    def test_save_and_load_yaml(self, temp_dir):
        """Test saving and loading YAML configuration"""
        config = MonitorConfig.create_example_config()
        file_path = Path(temp_dir) / "test.yaml"
        
        # Save config
        config.to_file(file_path)
        assert file_path.exists()
        
        # Load config
        loaded_config = MonitorConfig.from_file(file_path)
        
        assert loaded_config.log_level == config.log_level
        assert len(loaded_config.endpoints) == len(config.endpoints)
        assert len(loaded_config.notifications) == len(config.notifications)
    
    def test_save_and_load_json(self, temp_dir):
        """Test saving and loading JSON configuration"""
        config = MonitorConfig.create_example_config()
        file_path = Path(temp_dir) / "test.json"
        
        # Save config
        config.to_file(file_path)
        assert file_path.exists()
        
        # Load config
        loaded_config = MonitorConfig.from_file(file_path)
        
        assert loaded_config.log_level == config.log_level
        assert len(loaded_config.endpoints) == len(config.endpoints)
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent configuration file"""
        with pytest.raises(ConfigurationError):
            MonitorConfig.from_file("nonexistent.yaml")
    
    def test_invalid_yaml(self, temp_dir):
        """Test loading invalid YAML file"""
        file_path = Path(temp_dir) / "invalid.yaml"
        
        with open(file_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(ConfigurationError):
            MonitorConfig.from_file(file_path)
    
    def test_unsupported_format(self, temp_dir):
        """Test unsupported file format"""
        config = MonitorConfig()
        file_path = Path(temp_dir) / "test.txt"
        
        with pytest.raises(ConfigurationError):
            config.to_file(file_path)


class TestEnvConfig:
    
    def test_load_config_from_env_empty(self, monkeypatch):
        """Test loading config from environment with no variables"""
        # Clear relevant env vars
        for key in ["APIMONITOR_CONFIG", "APIMONITOR_URL"]:
            monkeypatch.delenv(key, raising=False)
        
        config = load_config_from_env()
        
        assert len(config.endpoints) == 0
        assert "console" in config.notifications
    
    def test_load_config_from_env_url(self, monkeypatch):
        """Test loading config from environment with URL"""
        monkeypatch.setenv("APIMONITOR_URL", "https://example.com")
        monkeypatch.setenv("APIMONITOR_TIMEOUT", "15")
        monkeypatch.setenv("APIMONITOR_INTERVAL", "120")
        
        config = load_config_from_env()
        
        assert len(config.endpoints) == 1
        assert config.endpoints[0].url == "https://example.com"
        assert config.endpoints[0].timeout_seconds == 15
        assert config.endpoints[0].check_interval_seconds == 120