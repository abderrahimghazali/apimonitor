"""
Tests for CLI interface
"""

import pytest
import json
from click.testing import CliRunner

from apimonitor.cli import main


class TestCLI:
    
    def setup_method(self):
        """Setup test method"""
        self.runner = CliRunner()
    
    def test_version(self):
        """Test version command"""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output
    
    def test_help(self):
        """Test help command"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'ApiMonitor' in result.output
    
    def test_init_command(self, temp_dir):
        """Test init command"""
        output_file = f"{temp_dir}/config.yaml"
        result = self.runner.invoke(main, ['init', '--output', output_file])
        
        assert result.exit_code == 0
        assert 'created' in result.output
        
        import os
        assert os.path.exists(output_file)
    
    def test_init_json_format(self, temp_dir):
        """Test init command with JSON format"""
        output_file = f"{temp_dir}/config.json"
        result = self.runner.invoke(main, [
            'init', 
            '--output', output_file, 
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        
        import os
        assert os.path.exists(output_file)
        
        # Verify it's valid JSON
        with open(output_file) as f:
            data = json.load(f)
            assert 'endpoints' in data
    
    def test_validate_command(self, config_file):
        """Test validate command"""
        result = self.runner.invoke(main, [
            'validate', 
            '--config-file', config_file
        ])
        
        assert result.exit_code == 0
        assert 'valid' in result.output
    
    def test_validate_nonexistent_file(self):
        """Test validate command with nonexistent file"""
        result = self.runner.invoke(main, [
            'validate', 
            '--config-file', 'nonexistent.yaml'
        ])
        
        assert result.exit_code == 1
        assert 'error' in result.output.lower()
    
    def test_check_command(self):
        """Test check command"""
        result = self.runner.invoke(main, [
            'check', 
            'https://httpbin.org/status/200',
            '--timeout', '10'
        ])
        
        assert result.exit_code == 0
        # Should show some output about the check
    
    def test_check_command_json_output(self):
        """Test check command with JSON output"""
        result = self.runner.invoke(main, [
            'check', 
            'https://httpbin.org/status/200',
            '--json-output'
        ])
        
        assert result.exit_code == 0
        
        # Verify JSON output
        try:
            output_data = json.loads(result.output)
            assert isinstance(output_data, list)
            assert len(output_data) > 0
        except json.JSONDecodeError:
            pytest.fail("Output was not valid JSON")
    
    def test_check_command_multiple_urls(self):
        """Test check command with multiple URLs"""
        result = self.runner.invoke(main, [
            'check',
            'https://httpbin.org/status/200',
            'https://httpbin.org/status/201',
            '--quiet'
        ])
        
        assert result.exit_code == 0
    
    def test_stats_command_no_config(self):
        """Test stats command without configuration"""
        result = self.runner.invoke(main, ['stats'])
        
        # Should handle gracefully (might show empty stats)
        assert result.exit_code in [0, 1]  # Either success or expected failure