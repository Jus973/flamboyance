"""Hybrid LLM routing layer.

Provides a unified interface for routing LLM calls between local Ollama
and cloud Groq providers based on task type.
"""

from .groq import call_groq
from .ollama import call_ollama
from .router import call_llm

__all__ = ["call_llm", "call_ollama", "call_groq"]
