"""Flamboyance: Spark-style master/worker/reducer orchestrator for LLM coding tasks."""

from .models import Task, WorkerResult, MergeResult, ImportGraph
from .master import Orchestrator

__all__ = ["Task", "WorkerResult", "MergeResult", "ImportGraph", "Orchestrator"]
__version__ = "0.1.0"
