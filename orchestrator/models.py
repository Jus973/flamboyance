"""Typed contracts shared between Master, Workers, and the Reducer.

These dataclasses are the *only* thing the components agree on. Everything
flowing across the orchestrator boundary (worker JSON payloads, results,
merge reports) round-trips through `to_dict` / `from_dict` so we keep the
interface stable even when components live in different processes.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Task:
    """A unit of refactor work that a single Worker can execute in isolation.

    Mirrors the JSON wire-format defined in `orchestrator_spec.md` §3.
    """

    task_id: str
    files_to_edit: tuple[str, ...]
    context_files: tuple[str, ...]
    instruction: str
    # Optional human-readable label used for branch names / logs.
    label: str = ""

    @classmethod
    def new(
        cls,
        files_to_edit: Iterable[str],
        context_files: Iterable[str],
        instruction: str,
        label: str = "",
    ) -> "Task":
        return cls(
            task_id=str(uuid.uuid4()),
            files_to_edit=tuple(sorted(set(files_to_edit))),
            context_files=tuple(sorted(set(context_files))),
            instruction=instruction,
            label=label or "task",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "files_to_edit": list(self.files_to_edit),
            "context_files": list(self.context_files),
            "instruction": self.instruction,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Task":
        return cls(
            task_id=payload["task_id"],
            files_to_edit=tuple(payload.get("files_to_edit", [])),
            context_files=tuple(payload.get("context_files", [])),
            instruction=payload["instruction"],
            label=payload.get("label", ""),
        )

    @property
    def branch_name(self) -> str:
        # Short, deterministic, filesystem-safe branch suffix.
        suffix = self.task_id.split("-")[0]
        slug = "".join(c if c.isalnum() else "-" for c in self.label).strip("-").lower()
        slug = slug[:24] or "task"
        return f"flamboyance/{slug}-{suffix}"


@dataclass
class WorkerResult:
    """Result returned by a Worker after running its task in a worktree."""

    task_id: str
    branch: str
    worktree_path: str
    status: str  # "success" | "failed" | "violation"
    modified_files: list[str] = field(default_factory=list)
    log: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MergeResult:
    """Outcome of integrating one Worker branch back into the trunk."""

    task_id: str
    branch: str
    status: str  # "merged" | "auto-resolved" | "conflict" | "skipped"
    conflicts: list[str] = field(default_factory=list)
    resolution_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImportGraph:
    """A lightweight module-level dependency graph for a Python codebase.

    Nodes are repo-relative POSIX paths. Edges go *from importer to importee*.
    Files outside the scanned root are silently ignored — we only care about
    intra-repo coupling for the purposes of independence checking.
    """

    root: Path
    files: list[str] = field(default_factory=list)
    edges: dict[str, set[str]] = field(default_factory=dict)
    reverse_edges: dict[str, set[str]] = field(default_factory=dict)

    def successors(self, node: str) -> set[str]:
        return self.edges.get(node, set())

    def predecessors(self, node: str) -> set[str]:
        return self.reverse_edges.get(node, set())

    def degree(self, node: str) -> int:
        return len(self.successors(node)) + len(self.predecessors(node))

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "files": self.files,
            "edges": {k: sorted(v) for k, v in self.edges.items()},
        }


def dump_json(obj: Any, path: Path) -> None:
    """Pretty-print JSON to disk; used for task manifests & worker payloads."""
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())
