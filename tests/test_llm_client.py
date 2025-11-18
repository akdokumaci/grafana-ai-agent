"""Tests for LLM client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from grafana_agent.llm_client import OpenAIClient, AnthropicClient, get_llm_client


class TestOpenAIClient:
    """Tests for OpenAI client."""
    
    def test_openai_client_init(self, mock_openai_client):
        """Test OpenAI client initialization."""
        client = OpenAIClient(api_key="test-key", model="gpt-4")
        assert client.model == "gpt-4"
    
    def test_openai_client_init_without_key(self, monkeypatch):
        """Test OpenAI client initialization with env var."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        with patch("openai.OpenAI") as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            client = OpenAIClient()
            mock_openai_class.assert_called_once_with(api_key="env-key")
    
    def test_openai_client_chat(self, mock_openai_client):
        """Test OpenAI client chat method."""
        client = OpenAIClient(api_key="test-key")
        messages = [{"role": "user", "content": "test"}]
        
        response = client.chat(messages)
        
        assert response is not None
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["messages"] == messages
    
    def test_openai_client_missing_package(self, monkeypatch):
        """Test error when openai package is missing."""
        import sys
        if 'openai' in sys.modules:
            monkeypatch.delitem(sys.modules, 'openai')
        
        with patch.dict('sys.modules', {'openai': None}):
            with pytest.raises(ImportError, match="openai package is required"):
                OpenAIClient()


class TestAnthropicClient:
    """Tests for Anthropic client."""
    
    def test_anthropic_client_init(self, mock_anthropic_client):
        """Test Anthropic client initialization."""
        client = AnthropicClient(api_key="test-key", model="claude-3-sonnet-20240229")
        assert client.model == "claude-3-sonnet-20240229"
    
    def test_anthropic_client_init_without_key(self, monkeypatch):
        """Test Anthropic client initialization with env var."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        with patch("anthropic.Anthropic") as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client
            client = AnthropicClient()
            mock_anthropic_class.assert_called_once_with(api_key="env-key")
    
    def test_anthropic_client_chat(self, mock_anthropic_client):
        """Test Anthropic client chat method."""
        client = AnthropicClient(api_key="test-key")
        messages = [{"role": "user", "content": "test"}]
        
        response = client.chat(messages)
        
        assert response is not None
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-sonnet-20240229"
        assert call_args[1]["messages"] == messages
    
    def test_anthropic_client_missing_package(self, monkeypatch):
        """Test error when anthropic package is missing."""
        import sys
        if 'anthropic' in sys.modules:
            monkeypatch.delitem(sys.modules, 'anthropic')
        
        with patch.dict('sys.modules', {'anthropic': None}):
            with pytest.raises(ImportError, match="anthropic package is required"):
                AnthropicClient()


class TestGetLLMClient:
    """Tests for LLM client factory function."""
    
    def test_get_openai_client(self, mock_openai_client):
        """Test getting OpenAI client."""
        client = get_llm_client("openai", api_key="test-key")
        assert isinstance(client, OpenAIClient)
    
    def test_get_anthropic_client(self, mock_anthropic_client):
        """Test getting Anthropic client."""
        client = get_llm_client("anthropic", api_key="test-key")
        assert isinstance(client, AnthropicClient)
    
    def test_get_unsupported_provider(self):
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_client("unsupported")
    
    def test_get_client_case_insensitive(self, mock_openai_client):
        """Test that provider name is case insensitive."""
        client1 = get_llm_client("OPENAI", api_key="test-key")
        client2 = get_llm_client("openai", api_key="test-key")
        assert type(client1) == type(client2)

