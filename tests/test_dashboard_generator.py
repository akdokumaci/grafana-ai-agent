"""Tests for dashboard generator."""

import pytest
import json
from unittest.mock import Mock, patch
from grafana_agent.dashboard_generator import DashboardGenerator


class TestDashboardGenerator:
    """Tests for dashboard generator."""
    
    def test_init(self, mock_llm_client):
        """Test dashboard generator initialization."""
        generator = DashboardGenerator(mock_llm_client)
        assert generator.llm_client == mock_llm_client
    
    def test_create_dashboard(self, mock_llm_client):
        """Test creating a dashboard."""
        mock_llm_client.chat.return_value = json.dumps({
            "dashboard": {
                "title": "Test Dashboard",
                "panels": [{"id": 1, "title": "Panel 1"}]
            }
        })
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard = generator.create_dashboard("Create a CPU monitoring dashboard")
        
        assert "dashboard" in dashboard
        assert dashboard["dashboard"]["title"] == "Test Dashboard"
        assert len(dashboard["dashboard"]["panels"]) == 1
        mock_llm_client.chat.assert_called_once()
    
    def test_create_dashboard_with_title(self, mock_llm_client):
        """Test creating a dashboard with custom title."""
        mock_llm_client.chat.return_value = json.dumps({
            "dashboard": {"title": "Custom Title", "panels": []}
        })
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard = generator.create_dashboard("Create dashboard", dashboard_title="Custom Title")
        
        assert dashboard["dashboard"]["title"] == "Custom Title"
    
    def test_create_dashboard_with_markdown_code_block(self, mock_llm_client):
        """Test handling LLM response with markdown code blocks."""
        mock_llm_client.chat.return_value = "```json\n" + json.dumps({
            "dashboard": {"title": "Test", "panels": []}
        }) + "\n```"
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard = generator.create_dashboard("Create dashboard")
        
        assert "dashboard" in dashboard
    
    def test_create_dashboard_ensures_required_fields(self, mock_llm_client):
        """Test that required dashboard fields are added."""
        mock_llm_client.chat.return_value = json.dumps({
            "dashboard": {"title": "Test"}
        })
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard = generator.create_dashboard("Create dashboard")
        
        dash = dashboard["dashboard"]
        assert "panels" in dash
        assert "time" in dash
        assert "timezone" in dash
        assert "schemaVersion" in dash
        assert "version" in dash
        assert "tags" in dash
        assert "uid" in dash
    
    def test_create_dashboard_wraps_if_needed(self, mock_llm_client):
        """Test that dashboard object is wrapped if needed."""
        mock_llm_client.chat.return_value = json.dumps({
            "title": "Test",
            "panels": []
        })
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard = generator.create_dashboard("Create dashboard")
        
        assert "dashboard" in dashboard
    
    def test_create_dashboard_invalid_json(self, mock_llm_client):
        """Test error handling for invalid JSON response."""
        mock_llm_client.chat.return_value = "This is not JSON"
        
        generator = DashboardGenerator(mock_llm_client)
        
        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            generator.create_dashboard("Create dashboard")
    
    def test_summarize_dashboard(self, mock_llm_client):
        """Test summarizing a dashboard."""
        mock_llm_client.chat.return_value = "This dashboard shows CPU and memory metrics."
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard_json = {
            "title": "Test Dashboard",
            "panels": [{"title": "CPU Usage"}]
        }
        
        summary = generator.summarize_dashboard(dashboard_json)
        
        assert summary == "This dashboard shows CPU and memory metrics."
        mock_llm_client.chat.assert_called_once()
        call_args = mock_llm_client.chat.call_args
        assert "Summarize this Grafana dashboard" in call_args[0][0][1]["content"]
    
    def test_summarize_dashboard_with_complex_structure(self, mock_llm_client):
        """Test summarizing a complex dashboard."""
        mock_llm_client.chat.return_value = "Complex dashboard summary"
        
        generator = DashboardGenerator(mock_llm_client)
        dashboard_json = {
            "dashboard": {
                "title": "Complex Dashboard",
                "panels": [
                    {"id": 1, "title": "Panel 1", "type": "graph"},
                    {"id": 2, "title": "Panel 2", "type": "stat"}
                ],
                "tags": ["monitoring", "production"]
            }
        }
        
        summary = generator.summarize_dashboard(dashboard_json)
        
        assert summary == "Complex dashboard summary"
        # Verify dashboard JSON is included in the prompt
        call_args = mock_llm_client.chat.call_args
        assert "Complex Dashboard" in call_args[0][0][1]["content"]

