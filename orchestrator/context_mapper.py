"""Context Mapper: scan a directory, build an import graph, and emit the
*minimum* file set needed for each refactor task.

The goal is twofold:
  1. **Token economy** — a Worker should never see files it doesn't need.
  2. **Independence proofs** — two tasks are safe to parallelize iff their
     edit sets are disjoint *and* there is no import edge between them
     (per spec §4: "if Task B depends on Task A's output, they must run
     sequentially or be fused").
"""

from __future__ import annotations

import ast
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import ImportGraph, Task

log = logging.getLogger(__name__)

# Heuristic markers a developer can drop into source code to nominate a file
# for refactoring. The mapper picks these up automatically.
TASK_MARKER_RE = re.compile(
    r"#\s*(?:REFACTOR|TASK|FLAMBOYANCE)\s*[:\-]\s*(.+?)\s*$",
    re.MULTILINE,
)

# Directory hints suggesting a file holds shared types / API contracts.
SHARED_DIR_HINTS = ("types", "typing", "models", "schemas", "protocols", "core", "api")

# Files we never scan or include as context.
EXCLUDE_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules",
    "build", "dist", ".flamboyance", ".mypy_cache", ".ruff_cache",
}


@dataclass
class TaskCandidate:
    """A refactor task discovered (or supplied) before context expansion."""

    label: str
    files: list[str]
    instruction: str


class ContextMapper:
    """Builds an import graph and derives task contexts from it."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    # ------------------------------------------------------------------ scan

    def scan(self) -> ImportGraph:
        """Walk `self.root`, parse every .py file, and return the import graph."""
        files = sorted(self._iter_py_files())
        graph = ImportGraph(root=self.root, files=files)

        # Pre-build a module -> file lookup so we can resolve `import foo.bar`.
        module_to_file: dict[str, str] = {}
        for rel in files:
            mod = self._file_to_module(rel)
            if mod:
                module_to_file[mod] = rel
                # Also register the package's __init__ shorthand.
                if rel.endswith("/__init__.py"):
                    pkg = mod.rsplit(".__init__", 1)[0] if mod.endswith(".__init__") else mod
                    module_to_file[pkg] = rel

        for rel in files:
            imports = self._extract_imports(self.root / rel, owning_module=self._file_to_module(rel))
            resolved = {
                module_to_file[m]
                for m in imports
                if m in module_to_file and module_to_file[m] != rel
            }
            graph.edges[rel] = resolved
            for tgt in resolved:
                graph.reverse_edges.setdefault(tgt, set()).add(rel)
        return graph

    def _iter_py_files(self) -> Iterable[str]:
        for p in self.root.rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in p.parts):
                continue
            yield p.relative_to(self.root).as_posix()

    def _file_to_module(self, rel: str) -> str | None:
        if not rel.endswith(".py"):
            return None
        mod = rel[:-3].replace("/", ".")
        if mod.endswith(".__init__"):
            mod = mod[: -len(".__init__")]
        return mod

    def _extract_imports(self, path: Path, owning_module: str | None) -> set[str]:
        """Return the set of fully-qualified module names imported by `path`."""
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError) as e:
            log.debug("Skipping %s (parse error): %s", path, e)
            return set()

        out: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    out.add(alias.name)
                    # Also register every parent package so "import a.b.c"
                    # resolves to a/b/c.py *or* a/b/__init__.py *or* a/__init__.py.
                    parts = alias.name.split(".")
                    for i in range(1, len(parts)):
                        out.add(".".join(parts[:i]))
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level and owning_module:
                    # Resolve relative imports against the owning module.
                    pkg_parts = owning_module.split(".")[: -node.level] if node.level <= len(owning_module.split(".")) else []
                    base = ".".join(filter(None, [*pkg_parts, base]))
                if base:
                    out.add(base)
                    for alias in node.names:
                        out.add(f"{base}.{alias.name}")
        return out

    # --------------------------------------------------------- shared context

    def shared_context(self, graph: ImportGraph, top_n: int = 5) -> list[str]:
        """Files that look like 'core' shared infra — heavily imported and/or
        living in a typings/models/api directory. Always added to every task's
        context so Workers don't invent incompatible signatures."""
        scores: Counter[str] = Counter()
        for f in graph.files:
            in_deg = len(graph.predecessors(f))
            scores[f] += in_deg * 2
            if any(hint in Path(f).parts for hint in SHARED_DIR_HINTS):
                scores[f] += 5
        # Drop files nobody imports — they aren't really "shared".
        ranked = [f for f, s in scores.most_common() if s > 0]
        return ranked[:top_n]

    # --------------------------------------------------- per-task context map

    def context_for(
        self,
        graph: ImportGraph,
        files_to_edit: Iterable[str],
        depth: int = 1,
        max_files: int = 12,
    ) -> list[str]:
        """Compute the minimum context set for a refactor on `files_to_edit`.

        We include:
          * every direct import (so Workers see the signatures they call), and
          * every direct importer (so Workers see how their symbols are used),
        bounded by `depth` hops and `max_files` to keep the prompt tight.
        """
        edit_set = set(files_to_edit)
        frontier = set(edit_set)
        visited: set[str] = set(edit_set)
        for _ in range(max(0, depth)):
            nxt: set[str] = set()
            for node in frontier:
                nxt |= graph.successors(node)
                nxt |= graph.predecessors(node)
            nxt -= visited
            visited |= nxt
            frontier = nxt
            if not frontier:
                break
        # Always layer in the global "shared" files.
        context = (visited - edit_set) | set(self.shared_context(graph))
        context -= edit_set
        # Stable ordering, capped.
        return sorted(context)[:max_files]

    # ---------------------------------------------------- task discovery

    def discover_candidates(self, graph: ImportGraph) -> list[TaskCandidate]:
        """Mine the codebase for refactor candidates.

        Strategy:
          1. Files containing a `# REFACTOR: ...` / `# TASK: ...` marker are
             treated as explicit nominations (instruction taken from the marker).
          2. Otherwise, fall back to the highest-out-degree leaf modules — they
             are the most "actionable" files to modernize without rippling.
        """
        candidates: list[TaskCandidate] = []
        seen: set[str] = set()

        # Pass 1: explicit markers.
        for rel in graph.files:
            text = (self.root / rel).read_text(encoding="utf-8", errors="replace")
            for m in TASK_MARKER_RE.finditer(text):
                instruction = m.group(1).strip()
                label = self._slug(Path(rel).stem)
                candidates.append(TaskCandidate(label=label, files=[rel], instruction=instruction))
                seen.add(rel)

        # Pass 2: fall back to leaf-y modules so we always have *something*.
        if len(candidates) < 3:
            leaf_scores = sorted(
                (rel for rel in graph.files if rel not in seen),
                key=lambda r: (-len(graph.successors(r)), len(graph.predecessors(r)), r),
            )
            for rel in leaf_scores:
                if len(candidates) >= 3:
                    break
                candidates.append(
                    TaskCandidate(
                        label=self._slug(Path(rel).stem),
                        files=[rel],
                        instruction=(
                            f"Modernize {rel}: add type hints, replace string "
                            f"concatenation with f-strings, and extract magic numbers."
                        ),
                    )
                )
        return candidates

    # ------------------------------------------------ independence selection

    def select_independent(
        self,
        graph: ImportGraph,
        candidates: list[TaskCandidate],
        n: int = 3,
    ) -> list[TaskCandidate]:
        """Greedy DAG-aware selection: pick `n` candidates whose edit sets are
        mutually disjoint AND have no direct import edges between them."""
        chosen: list[TaskCandidate] = []
        chosen_files: set[str] = set()

        for cand in candidates:
            cand_files = set(cand.files)
            if cand_files & chosen_files:
                continue  # overlapping edits → would race
            if self._has_dependency(graph, cand_files, chosen_files):
                continue  # B imports A → must run sequentially
            chosen.append(cand)
            chosen_files |= cand_files
            if len(chosen) >= n:
                break
        return chosen

    def _has_dependency(
        self,
        graph: ImportGraph,
        a: set[str],
        b: set[str],
    ) -> bool:
        for f in a:
            if graph.successors(f) & b or graph.predecessors(f) & b:
                return True
        return False

    # ---------------------------------------------------------- helpers

    @staticmethod
    def _slug(s: str) -> str:
        return "".join(c if c.isalnum() else "-" for c in s).strip("-").lower() or "task"

    # ------------------------------------------------- public convenience

    def build_tasks(self, n: int = 3) -> tuple[ImportGraph, list[Task]]:
        """One-shot helper used by the Master: scan → discover → select → bind context."""
        graph = self.scan()
        candidates = self.discover_candidates(graph)
        independent = self.select_independent(graph, candidates, n=n)
        tasks = [
            Task.new(
                files_to_edit=c.files,
                context_files=self.context_for(graph, c.files),
                instruction=c.instruction,
                label=c.label,
            )
            for c in independent
        ]
        return graph, tasks
