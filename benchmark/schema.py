"""Schema definitions for benchmark ground truth and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroundTruthIssue:
    """A manually annotated UX issue in a test app."""
    
    id: str
    type: str
    severity: str
    url_pattern: str
    description: str
    selector: str | None = None
    keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroundTruthIssue":
        return cls(
            id=data["id"],
            type=data["type"],
            severity=data["severity"],
            url_pattern=data["url_pattern"],
            description=data["description"],
            selector=data.get("selector"),
            keywords=data.get("keywords", []),
        )


@dataclass
class GroundTruth:
    """Ground truth annotations for a test app."""
    
    app: str
    port: int
    annotator: str
    date: str
    description: str
    issues: list[GroundTruthIssue]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroundTruth":
        return cls(
            app=data["app"],
            port=data["port"],
            annotator=data["annotator"],
            date=data["date"],
            description=data["description"],
            issues=[GroundTruthIssue.from_dict(i) for i in data["issues"]],
        )


@dataclass
class DetectedIssue:
    """An issue detected by a tool."""
    
    type: str
    url: str
    description: str
    severity: str = "medium"
    persona: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchResult:
    """Result of matching a detected issue to ground truth."""
    
    detected: DetectedIssue
    ground_truth: GroundTruthIssue | None
    matched: bool
    match_score: float = 0.0


@dataclass
class BenchmarkResult:
    """Results from running a benchmark on one app."""
    
    app: str
    tool: str
    run_id: str
    detected_issues: list[DetectedIssue]
    ground_truth: GroundTruth
    matches: list[MatchResult] = field(default_factory=list)
    
    # Computed metrics
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
