#!/usr/bin/env python3
"""
Integration tests for UBDF CLI commands
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import json

from ubdf.cli.main import cli


class TestCLICommands:
    """Test CLI command functionality"""
    
    def test_cli_init_command(self, temp_workspace):
        """Test ubdf init command"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'])
            
            assert result.exit_code == 0
            assert "UBDF Workspace Initialized" in result.output
            assert Path("reports").exists()
            assert Path("configs").exists()
    
    def test_cli_scan_command(self, temp_workspace):
        """Test ubdf scan command"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['scan', '--manufacturer', 'milwaukee'])
            
            assert result.exit_code == 0
            assert "Battery Discovery Scan" in result.output
            # Mock scan should find simulated battery
            assert "Milwaukee" in result.output or "No batteries discovered" in result.output
    
    def test_cli_scan_with_output(self, temp_workspace):
        """Test scan command with output file"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['scan', '--output', 'scan_results.json'])
            
            assert result.exit_code == 0
            if Path("scan_results.json").exists():
                with open("scan_results.json") as f:
                    scan_data = json.load(f)
                assert isinstance(scan_data, list)
    
    def test_cli_help_commands(self):
        """Test help output for all commands"""
        runner = CliRunner()
        
        # Test main help
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Universal Battery Diagnostics Framework" in result.output
        
        # Test subcommand help
        commands = ['scan', 'init']
        for cmd in commands:
            result = runner.invoke(cli, [cmd, '--help'])
            assert result.exit_code == 0
    
    def test_cli_version(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output