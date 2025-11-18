"""Tests for Grafana client."""

import pytest
from unittest.mock import Mock, patch
from grafana_agent.grafana_client import GrafanaClient


class TestGrafanaClient:
    """Tests for Grafana client."""
    
    def test_init_with_api_key(self, mock_requests):
        """Test initialization with API key."""
        client = GrafanaClient("http://localhost:3000", api_key="test-key")
        assert client.base_url == "http://localhost:3000"
        assert client.api_key == "test-key"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test-key"
    
    def test_init_with_username_password(self, mock_requests):
        """Test initialization with username/password."""
        client = GrafanaClient("http://localhost:3000", username="admin", password="admin")
        assert client.base_url == "http://localhost:3000"
        assert client.username == "admin"
        assert client.password == "admin"
        assert client.session.auth == ("admin", "admin")
    
    def test_init_without_credentials(self):
        """Test error when no credentials provided."""
        with pytest.raises(ValueError, match="Either api_key or username/password"):
            GrafanaClient("http://localhost:3000")
    
    def test_init_strips_trailing_slash(self, mock_requests):
        """Test that base URL trailing slash is stripped."""
        client = GrafanaClient("http://localhost:3000/", api_key="test-key")
        assert client.base_url == "http://localhost:3000"
    
    def test_create_dashboard(self, mock_requests):
        """Test creating a dashboard."""
        client = GrafanaClient("http://localhost:3000", api_key="test-key")
        dashboard = {"title": "Test Dashboard", "panels": []}
        
        result = client.create_dashboard(dashboard, folder_id=1, overwrite=True)
        
        assert result is not None
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "POST"
        assert "/api/dashboards/db" in call_args[0][1]
        assert call_args[1]["json"]["dashboard"] == dashboard
        assert call_args[1]["json"]["folderId"] == 1
        assert call_args[1]["json"]["overwrite"] is True
    
    def test_get_dashboard(self, mock_requests):
        """Test getting a dashboard."""
        client = GrafanaClient("http://localhost:3000", api_key="test-key")
        
        result = client.get_dashboard("test-uid")
        
        assert result is not None
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "GET"
        assert "/api/dashboards/uid/test-uid" in call_args[0][1]
    
    def test_search_dashboards(self, mock_requests):
        """Test searching dashboards."""
        client = GrafanaClient("http://localhost:3000", api_key="test-key")
        
        # Mock search response
        mock_response = Mock()
        mock_response.json.return_value = [{"uid": "dashboard1"}, {"uid": "dashboard2"}]
        mock_response.raise_for_status = Mock()
        mock_requests.request.return_value = mock_response
        
        result = client.search_dashboards(query="test", tag="monitoring", limit=50)
        
        assert len(result) == 2
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "GET"
        assert "/api/search" in call_args[0][1]
        assert call_args[1]["params"]["query"] == "test"
        assert call_args[1]["params"]["tag"] == "monitoring"
        assert call_args[1]["params"]["limit"] == 50
    
    def test_delete_dashboard(self, mock_requests):
        """Test deleting a dashboard."""
        client = GrafanaClient("http://localhost:3000", api_key="test-key")
        
        client.delete_dashboard("test-uid")
        
        mock_requests.request.assert_called_once()
        call_args = mock_requests.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/api/dashboards/uid/test-uid" in call_args[0][1]
    
    def test_request_error_handling(self, mock_requests):
        """Test error handling for API requests."""
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("Not found")
        mock_requests.request.return_value = mock_response
        
        client = GrafanaClient("http://localhost:3000", api_key="test-key")
        
        with pytest.raises(requests.HTTPError):
            client.get_dashboard("nonexistent")

