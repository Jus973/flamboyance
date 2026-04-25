# Specification: Distributed Coding Orchestrator (Spark-Model)

## 1. Goal
Create a CLI-based master-worker system that parallelizes coding tasks to maximize throughput and minimize context-drift hallucinations.

## 2. Core Components
- **The Master (Driver):** - Scans the codebase.
    - Generates a Task DAG (Directed Acyclic Graph) in JSON format.
    - Identifies "Shared Context" (Core Types/API) vs "Local Context" (File-specific logic).
- **The Worker (Executor):**
    - Stateless and ephemeral.
    - Operates within a temporary Git Worktree.
    - Executes specialized refactor instructions.
- **The Reducer (Integrator):**
    - Merges worktrees back to the main branch.
    - Runs a global `linter` and `test` suite to ensure integration integrity.

## 3. Communication Protocol (JSON)
Workers must receive:
{
  "task_id": "uuid",
  "files_to_edit": ["path/to/file"],
  "context_files": ["path/to/shared/types"],
  "instruction": "Detailed refactor prompt"
}

## 4. Constraint & Safety
- Workers MUST NOT modify files outside their assigned `files_to_edit` list.
- Master MUST perform a "Dependency Check" before parallelizing; if Task B depends on Task A's output, they must run sequentially or be fused.