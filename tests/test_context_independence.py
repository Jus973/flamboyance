"""Tests for the Context Mapper's independence guarantee (spec §4)."""

import textwrap
from pathlib import Path

from orchestrator.context_mapper import ContextMapper


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(body))


def test_dependent_tasks_are_dropped(tmp_path: Path):
    _write(tmp_path, {
        "core/types.py": "class T: pass\n",
        "a.py": "# TASK: rewrite a\nfrom core.types import T\n",
        "b.py": "# TASK: rewrite b\nimport a  # depends on a\n",
        "c.py": "# TASK: rewrite c\n",
    })
    mapper = ContextMapper(tmp_path)
    graph = mapper.scan()

    # b.py imports a.py → they cannot run in parallel. The Mapper must keep
    # the first one it saw and drop the dependent one.
    candidates = mapper.discover_candidates(graph)
    chosen = mapper.select_independent(graph, candidates, n=3)
    chosen_files = {f for c in chosen for f in c.files}
    assert not ("a.py" in chosen_files and "b.py" in chosen_files), (
        "Mapper allowed two tasks with an import edge to run in parallel"
    )
    # c.py is unrelated so it MUST be in the parallel batch.
    assert "c.py" in chosen_files


def test_minimum_context_includes_imports_and_importers(tmp_path: Path):
    _write(tmp_path, {
        "shared/types.py": "class User: pass\n",
        "lib/svc.py": "from shared.types import User\nclass Svc: pass\n",
        "app.py": "from lib.svc import Svc\n",
        "unrelated.py": "X = 1\n",
    })
    mapper = ContextMapper(tmp_path)
    graph = mapper.scan()
    ctx = mapper.context_for(graph, ["lib/svc.py"])
    # Should include the imported module (shared/types.py) and the importer (app.py).
    assert "shared/types.py" in ctx
    assert "app.py" in ctx
    # Should NOT drag in completely unrelated files when depth=1.
    assert "unrelated.py" not in ctx
