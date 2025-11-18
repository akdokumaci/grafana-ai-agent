"""Dashboard generator using LLM to create Grafana dashboards."""

import json
from typing import Dict, Any, Optional
from .llm_client import LLMClient


class DashboardGenerator:
    """Generate Grafana dashboards using LLM."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize dashboard generator.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for dashboard generation."""
        return """You are an expert at creating Grafana dashboards. You understand Grafana's dashboard JSON schema and can create comprehensive, well-structured dashboards.

When creating a dashboard, you should:
1. Include proper metadata (title, tags, timezone, etc.)
2. Create appropriate panels (graph, stat, table, etc.)
3. Use proper data source queries
4. Add useful visualizations
5. Include time range controls
6. Make the dashboard user-friendly

Always respond with valid JSON that follows Grafana's dashboard schema. Return ONLY the JSON, no markdown formatting or explanations."""

    def _get_summarize_prompt(self) -> str:
        """Get the system prompt for dashboard summarization."""
        return """You are an expert at analyzing Grafana dashboards. You can read dashboard JSON and provide clear, concise summaries.

When summarizing a dashboard, you should:
1. Describe the dashboard's purpose
2. List the main panels and what they show
3. Identify the data sources used
4. Note any important features or configurations
5. Provide insights about the dashboard's structure

Be clear and concise in your summary."""

    def create_dashboard(self, user_request: str, dashboard_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a Grafana dashboard based on user request.
        
        Args:
            user_request: User's description of what they want in the dashboard
            dashboard_title: Optional title for the dashboard
        
        Returns:
            Dashboard JSON object
        """
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Create a Grafana dashboard for: {user_request}" + 
             (f"\nTitle: {dashboard_title}" if dashboard_title else "")}
        ]
        
        response = self.llm_client.chat(messages, temperature=0.3)
        
        # Try to extract JSON from response (handle markdown code blocks)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        try:
            dashboard = json.loads(response)
            
            # Ensure basic structure
            if "dashboard" not in dashboard:
                # If LLM returned just the dashboard object, wrap it
                if "title" in dashboard or "panels" in dashboard:
                    dashboard = {"dashboard": dashboard}
            
            # Ensure dashboard has required fields
            if "dashboard" in dashboard:
                dash = dashboard["dashboard"]
                if "title" not in dash:
                    dash["title"] = dashboard_title or "Generated Dashboard"
                if "uid" not in dash:
                    dash["uid"] = dash["title"].lower().replace(" ", "-")
                if "panels" not in dash:
                    dash["panels"] = []
                if "time" not in dash:
                    dash["time"] = {"from": "now-6h", "to": "now"}
                if "timezone" not in dash:
                    dash["timezone"] = "browser"
                if "schemaVersion" not in dash:
                    dash["schemaVersion"] = 38
                if "version" not in dash:
                    dash["version"] = 0
                if "tags" not in dash:
                    dash["tags"] = []
            
            return dashboard
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {response}")
    
    def summarize_dashboard(self, dashboard_json: Dict[str, Any]) -> str:
        """
        Generate a summary of a Grafana dashboard.
        
        Args:
            dashboard_json: Dashboard JSON object
        
        Returns:
            Summary text
        """
        messages = [
            {"role": "system", "content": self._get_summarize_prompt()},
            {"role": "user", "content": f"Summarize this Grafana dashboard:\n{json.dumps(dashboard_json, indent=2)}"}
        ]
        
        response = self.llm_client.chat(messages, temperature=0.3)
        return response.strip()

