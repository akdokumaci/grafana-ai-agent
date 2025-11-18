"""Grafana API client for dashboard operations."""

import json
import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin


class GrafanaClient:
    """Client for interacting with Grafana API."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, username: Optional[str] = None, 
                 password: Optional[str] = None):
        """
        Initialize Grafana client.
        
        Args:
            base_url: Base URL of Grafana instance (e.g., 'http://localhost:3000')
            api_key: API key for authentication (preferred)
            username: Username for basic auth (if no API key)
            password: Password for basic auth (if no API key)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
        elif username and password:
            self.session.auth = (username, password)
            self.session.headers.update({'Content-Type': 'application/json'})
        else:
            raise ValueError("Either api_key or username/password must be provided")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request to the Grafana API."""
        url = urljoin(self.base_url, endpoint)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def create_dashboard(self, dashboard: Dict[str, Any], folder_id: int = 0, 
                        overwrite: bool = False) -> Dict[str, Any]:
        """
        Create or update a dashboard in Grafana.
        
        Args:
            dashboard: Dashboard JSON object
            folder_id: Folder ID to place dashboard in (0 for General)
            overwrite: Whether to overwrite if dashboard exists
        
        Returns:
            Dashboard creation response
        """
        payload = {
            "dashboard": dashboard,
            "folderId": folder_id,
            "overwrite": overwrite
        }
        response = self._request('POST', '/api/dashboards/db', json=payload)
        return response.json()
    
    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """
        Get a dashboard by UID.
        
        Args:
            uid: Dashboard UID
        
        Returns:
            Dashboard JSON object
        """
        response = self._request('GET', f'/api/dashboards/uid/{uid}')
        return response.json()
    
    def search_dashboards(self, query: str = "", tag: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for dashboards.
        
        Args:
            query: Search query
            tag: Filter by tag
            limit: Maximum number of results
        
        Returns:
            List of dashboard metadata
        """
        params = {
            "query": query,
            "tag": tag,
            "limit": limit
        }
        response = self._request('GET', '/api/search', params=params)
        return response.json()
    
    def delete_dashboard(self, uid: str) -> None:
        """
        Delete a dashboard by UID.
        
        Args:
            uid: Dashboard UID
        """
        self._request('DELETE', f'/api/dashboards/uid/{uid}')

