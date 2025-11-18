"""Tests for CLI interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from grafana_agent.cli import cli


class TestCLI:
    """Tests for CLI commands."""
    
    def test_cli_group(self):
        """Test that CLI group is accessible."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Grafana AI Agent" in result.output
    
    def test_cli_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    @patch('grafana_agent.cli.get_llm_client')
    @patch('grafana_agent.cli.ChatInterface')
    def test_chat_command_help(self, mock_chat_interface, mock_get_llm):
        """Test chat command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['chat', '--help'])
        assert result.exit_code == 0
        assert "Start an interactive conversational chat session" in result.output
    
    @patch('grafana_agent.cli.get_llm_client')
    @patch('grafana_agent.cli.ChatInterface')
    def test_create_command_help(self, mock_chat_interface, mock_get_llm):
        """Test create command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['create', '--help'])
        assert result.exit_code == 0
        assert "Create a Grafana dashboard from a description" in result.output
    
    @patch('grafana_agent.cli.get_llm_client')
    @patch('grafana_agent.cli.DashboardGenerator')
    def test_create_command(self, mock_generator_class, mock_get_llm):
        """Test create command execution."""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        mock_generator = Mock()
        mock_generator.create_dashboard.return_value = {
            "dashboard": {"title": "Test Dashboard", "panels": []}
        }
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'create',
            'test description',
            '--output', 'test_output.json'
        ])
        
        assert result.exit_code == 0
        mock_generator.create_dashboard.assert_called_once_with("test description", None)
    
    @patch('grafana_agent.cli.get_llm_client')
    @patch('grafana_agent.cli.DashboardGenerator')
    def test_create_command_with_title(self, mock_generator_class, mock_get_llm):
        """Test create command with title."""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        mock_generator = Mock()
        mock_generator.create_dashboard.return_value = {
            "dashboard": {"title": "Custom Title", "panels": []}
        }
        mock_generator_class.return_value = mock_generator
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'create',
            'test description',
            '--title', 'Custom Title'
        ])
        
        assert result.exit_code == 0
        mock_generator.create_dashboard.assert_called_once_with("test description", "Custom Title")
    
    @patch('grafana_agent.cli.get_llm_client')
    @patch('grafana_agent.cli.DashboardGenerator')
    def test_summarize_command(self, mock_generator_class, mock_get_llm, tmp_path):
        """Test summarize command."""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        mock_generator = Mock()
        mock_generator.summarize_dashboard.return_value = "Test summary"
        mock_generator_class.return_value = mock_generator
        
        # Create a test dashboard file
        test_file = tmp_path / "test_dashboard.json"
        test_file.write_text('{"title": "Test Dashboard", "panels": []}')
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'summarize',
            str(test_file)
        ])
        
        assert result.exit_code == 0
        assert "Test summary" in result.output
        mock_generator.summarize_dashboard.assert_called_once()
    
    @patch('grafana_agent.cli.get_llm_client')
    def test_create_command_missing_llm(self, mock_get_llm):
        """Test create command error handling."""
        mock_get_llm.side_effect = ImportError("Missing package")
        
        runner = CliRunner()
        result = runner.invoke(cli, ['create', 'test'])
        
        assert result.exit_code == 1
        assert "Error initializing LLM client" in result.output
    
    @patch('grafana_agent.cli.get_llm_client')
    @patch('grafana_agent.cli.DashboardGenerator')
    def test_summarize_command_file_not_found(self, mock_generator_class, mock_get_llm):
        """Test summarize command with non-existent file."""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        runner = CliRunner()
        result = runner.invoke(cli, ['summarize', 'nonexistent.json'])
        
        # Click returns exit code 2 for invalid file path (exists=True validation)
        assert result.exit_code == 2

