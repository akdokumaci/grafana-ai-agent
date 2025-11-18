"""Tests for chat interface."""

import pytest
from unittest.mock import Mock, MagicMock
from grafana_agent.chat_interface import ChatInterface
from grafana_agent.dashboard_generator import DashboardGenerator


class TestChatInterface:
    """Tests for chat interface."""
    
    def test_init(self, mock_llm_client):
        """Test chat interface initialization."""
        interface = ChatInterface(mock_llm_client)
        assert interface.llm_client == mock_llm_client
        assert interface.grafana_client is None
        assert isinstance(interface.dashboard_generator, DashboardGenerator)
        assert len(interface.conversation_history) == 0
    
    def test_init_with_grafana_client(self, mock_llm_client, mock_requests):
        """Test initialization with Grafana client."""
        from grafana_agent.grafana_client import GrafanaClient
        grafana_client = GrafanaClient("http://localhost:3000", api_key="test-key")
        
        interface = ChatInterface(mock_llm_client, grafana_client)
        assert interface.grafana_client == grafana_client
    
    def test_chat(self, mock_llm_client):
        """Test basic chat functionality."""
        mock_llm_client.chat.return_value = "Hello! How can I help you?"
        
        interface = ChatInterface(mock_llm_client)
        response = interface.chat("Hello")
        
        assert response == "Hello! How can I help you?"
        assert len(interface.conversation_history) == 2  # user + assistant
        mock_llm_client.chat.assert_called_once()
    
    def test_chat_conversation_history(self, mock_llm_client):
        """Test that conversation history is maintained."""
        mock_llm_client.chat.side_effect = [
            "First response",
            "Second response"
        ]
        
        interface = ChatInterface(mock_llm_client)
        interface.chat("First message")
        interface.chat("Second message")
        
        assert len(interface.conversation_history) == 4  # 2 user + 2 assistant
        assert interface.conversation_history[0]["content"] == "First message"
        assert interface.conversation_history[1]["content"] == "First response"
        assert interface.conversation_history[2]["content"] == "Second message"
        assert interface.conversation_history[3]["content"] == "Second response"
    
    def test_chat_includes_system_prompt(self, mock_llm_client):
        """Test that system prompt is included in chat."""
        mock_llm_client.chat.return_value = "Response"
        
        interface = ChatInterface(mock_llm_client)
        interface.chat("Test message")
        
        call_args = mock_llm_client.chat.call_args
        messages = call_args[0][0]
        assert messages[0]["role"] == "system"
        assert "helpful assistant" in messages[0]["content"].lower()
    
    def test_create_dashboard(self, mock_llm_client):
        """Test creating dashboard through chat interface."""
        import json
        mock_llm_client.chat.return_value = json.dumps({
            "dashboard": {"title": "Test", "panels": []}
        })
        
        interface = ChatInterface(mock_llm_client)
        dashboard = interface.create_dashboard("Create a test dashboard")
        
        assert "dashboard" in dashboard
        assert dashboard["dashboard"]["title"] == "Test"
    
    def test_create_dashboard_with_title(self, mock_llm_client):
        """Test creating dashboard with title."""
        import json
        mock_llm_client.chat.return_value = json.dumps({
            "dashboard": {"title": "Custom Title", "panels": []}
        })
        
        interface = ChatInterface(mock_llm_client)
        dashboard = interface.create_dashboard("Create dashboard", title="Custom Title")
        
        assert dashboard["dashboard"]["title"] == "Custom Title"
    
    def test_summarize_dashboard(self, mock_llm_client):
        """Test summarizing dashboard through chat interface."""
        mock_llm_client.chat.return_value = "This is a test dashboard summary."
        
        interface = ChatInterface(mock_llm_client)
        dashboard_json = {"title": "Test Dashboard", "panels": []}
        
        summary = interface.summarize_dashboard(dashboard_json)
        
        assert summary == "This is a test dashboard summary."
    
    def test_reset_conversation(self, mock_llm_client):
        """Test resetting conversation history."""
        mock_llm_client.chat.return_value = "Response"
        
        interface = ChatInterface(mock_llm_client)
        interface.chat("Message 1")
        interface.chat("Message 2")
        
        assert len(interface.conversation_history) == 4
        
        interface.reset_conversation()
        
        assert len(interface.conversation_history) == 0

