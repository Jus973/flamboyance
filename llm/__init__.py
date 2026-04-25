"""Hybrid LLM routing layer.

Provides a unified interface for routing LLM calls between local Ollama
and cloud Groq providers based on task type.
"""

from .router import call_llm
from .ollama import call_ollama
from .groq import call_groq

__all__ = ["call_llm", "call_ollama", "call_groq"]
