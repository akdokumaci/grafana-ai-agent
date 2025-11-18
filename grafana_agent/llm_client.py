"""LLM client for conversational interactions."""

import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat message and get a response."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI client implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat message and get a response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content


class AnthropicClient(LLMClient):
    """Anthropic Claude client implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat message and get a response."""
        response = self.client.messages.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.content[0].text


def get_llm_client(provider: str = "openai", **kwargs) -> LLMClient:
    """Factory function to get an LLM client."""
    provider = provider.lower()
    
    if provider == "openai":
        return OpenAIClient(**kwargs)
    elif provider == "anthropic":
        return AnthropicClient(**kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: openai, anthropic")

