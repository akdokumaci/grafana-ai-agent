"""Conversational chat interface for dashboard operations."""

from typing import Optional, Dict, Any
from .llm_client import LLMClient
from .dashboard_generator import DashboardGenerator
from .grafana_client import GrafanaClient


class ChatInterface:
    """Conversational interface for interacting with Grafana dashboards."""
    
    def __init__(self, llm_client: LLMClient, grafana_client: Optional[GrafanaClient] = None):
        """
        Initialize chat interface.
        
        Args:
            llm_client: LLM client for conversations
            grafana_client: Optional Grafana client for direct operations
        """
        self.llm_client = llm_client
        self.grafana_client = grafana_client
        self.dashboard_generator = DashboardGenerator(llm_client)
        self.conversation_history = []
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the chat interface."""
        return """You are a helpful assistant that helps users create and manage Grafana dashboards. 

You can:
1. Create new Grafana dashboards based on user descriptions
2. Summarize existing dashboards
3. Answer questions about Grafana dashboards
4. Help users understand dashboard configurations

Be friendly, helpful, and provide clear explanations. When creating dashboards, ask clarifying questions if needed about:
- What metrics/data sources they want to visualize
- What type of panels they prefer
- Time ranges and refresh intervals
- Any specific requirements

If the user wants to create a dashboard, use the create_dashboard function. If they want to summarize a dashboard, use the summarize_dashboard function."""

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return a response.
        
        Args:
            user_message: User's message
        
        Returns:
            Assistant's response
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Build messages with system prompt
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        messages.extend(self.conversation_history)
        
        # Get response from LLM
        response = self.llm_client.chat(messages, temperature=0.7)
        
        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def create_dashboard(self, description: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a dashboard based on description.
        
        Args:
            description: Description of the dashboard
            title: Optional title
        
        Returns:
            Dashboard JSON
        """
        return self.dashboard_generator.create_dashboard(description, title)
    
    def summarize_dashboard(self, dashboard_json: Dict[str, Any]) -> str:
        """
        Summarize a dashboard.
        
        Args:
            dashboard_json: Dashboard JSON
        
        Returns:
            Summary text
        """
        return self.dashboard_generator.summarize_dashboard(dashboard_json)
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []

