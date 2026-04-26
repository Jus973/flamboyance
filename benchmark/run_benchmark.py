"""Benchmark runner for measuring Flamboyance detection accuracy."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

from benchmark.matcher import compute_metrics
from benchmark.schema import BenchmarkResult, DetectedIssue, GroundTruth

log = logging.getLogger(__name__)

BENCHMARK_DIR = Path(__file__).parent
APPS_DIR = BENCHMARK_DIR / "apps"
GROUND_TRUTH_DIR = BENCHMARK_DIR / "ground_truth"
RESULTS_DIR = BENCHMARK_DIR / "results"


def load_ground_truth(app_name: str) -> GroundTruth:
    """Load ground truth annotations for an app."""
    path = GROUND_TRUTH_DIR / f"{app_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No ground truth found for {app_name}")
    
    with open(path) as f:
        data = json.load(f)
    
    return GroundTruth.from_dict(data)


def start_app(app_name: str, port: int) -> subprocess.Popen:
    """Start a test app and return the process."""
    app_dir = APPS_DIR / app_name
    if not app_dir.exists():
        raise FileNotFoundError(f"App not found: {app_dir}")
    
    log.info(f"Starting {app_name} on port {port}...")
    
    # Install dependencies if needed
    if not (app_dir / "node_modules").exists():
        log.info(f"Installing dependencies for {app_name}...")
        subprocess.run(
            ["npm", "install"],
            cwd=app_dir,
            capture_output=True,
            check=True,
        )
    
    # Start the dev server
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=app_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to be ready
    time.sleep(3)
    
    return proc


def stop_app(proc: subprocess.Popen) -> None:
    """Stop a test app process."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


async def run_flamboyance(url: str, timeout: int = 60) -> dict:
    """Run Flamboyance against a URL and return results."""
    from agents.runner_local import run_local
    
    run_id = f"benchmark-{int(time.time())}"
    
    state = await run_local(
        url,
        persona_names=None,  # Use all personas
        timeout_s=timeout,
        run_id=run_id,
        llm_mode=True,
        max_llm_calls=20,
        headless=True,
        batch_size=3,
    )
    
    return {
        "run_id": run_id,
        "state": state,
    }


def extract_issues_from_flamboyance(state) -> list[DetectedIssue]:
    """Extract detected issues from Flamboyance run state."""
    issues = []
    
    for result in state.results:
        for event in result.frustration_events:
            issues.append(DetectedIssue(
                type=event.get("type", "unknown"),
                url=event.get("url", ""),
                description=event.get("description", ""),
                severity=event.get("severity", "medium"),
                persona=result.persona,
                raw=event,
            ))
    
    return issues


def parse_devin_output(app_name: str) -> list[DetectedIssue]:
    """Parse Devin's response from saved markdown file."""
    devin_dir = BENCHMARK_DIR / "devin_outputs"
    path = devin_dir / f"{app_name}.md"
    
    if not path.exists():
        log.warning(f"No Devin output found for {app_name}")
        return []
    
    issues = []
    content = path.read_text()
    
    # Simple parsing: look for bullet points with issue descriptions
    # Format expected: "- **type**: description (URL: /path)"
    import re
    
    pattern = r"[-*]\s*\*?\*?(\w+)\*?\*?:?\s*(.+?)(?:\(URL:\s*([^\)]+)\))?"
    
    for match in re.finditer(pattern, content, re.MULTILINE):
        issue_type = match.group(1).lower().replace(" ", "_")
        description = match.group(2).strip()
        url = match.group(3) or ""
        
        issues.append(DetectedIssue(
            type=issue_type,
            url=url,
            description=description,
            severity="medium",
            persona=None,
            raw={"source": "devin"},
        ))
    
    return issues


async def run_benchmark_for_app(
    app_name: str,
    tool: str = "flamboyance",
    skip_start: bool = False,
) -> BenchmarkResult:
    """Run benchmark for a single app."""
    
    ground_truth = load_ground_truth(app_name)
    url = f"http://localhost:{ground_truth.port}"
    
    proc = None
    if not skip_start:
        try:
            proc = start_app(app_name, ground_truth.port)
        except FileNotFoundError as e:
            log.error(f"Could not start app: {e}")
            raise
    
    try:
        if tool == "flamboyance":
            result = await run_flamboyance(url)
            detected = extract_issues_from_flamboyance(result["state"])
            run_id = result["run_id"]
        elif tool == "devin":
            detected = parse_devin_output(app_name)
            run_id = "devin-manual"
        else:
            raise ValueError(f"Unknown tool: {tool}")
        
        metrics = compute_metrics(detected, ground_truth)
        metrics.tool = tool
        metrics.run_id = run_id
        
        return metrics
        
    finally:
        if proc:
            stop_app(proc)


def save_results(results: list[BenchmarkResult]) -> Path:
    """Save benchmark results to JSON."""
    RESULTS_DIR.mkdir(exist_ok=True)
    
    timestamp = int(time.time())
    path = RESULTS_DIR / f"benchmark-{timestamp}.json"
    
    data = {
        "timestamp": timestamp,
        "results": [
            {
                "app": r.app,
                "tool": r.tool,
                "run_id": r.run_id,
                "precision": r.precision,
                "recall": r.recall,
                "f1": r.f1,
                "true_positives": r.true_positives,
                "false_positives": r.false_positives,
                "false_negatives": r.false_negatives,
                "detected_count": len(r.detected_issues),
                "ground_truth_count": len(r.ground_truth.issues),
            }
            for r in results
        ],
    }
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    
    log.info(f"Results saved to {path}")
    return path


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results to console."""
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    for r in results:
        print(f"\n{r.app} ({r.tool})")
        print("-" * 40)
        print(f"  Precision: {r.precision:.1%}")
        print(f"  Recall:    {r.recall:.1%}")
        print(f"  F1 Score:  {r.f1:.1%}")
        print(f"  TP: {r.true_positives} | FP: {r.false_positives} | FN: {r.false_negatives}")
        print(f"  Detected: {len(r.detected_issues)} | Ground Truth: {len(r.ground_truth.issues)}")
    
    # Aggregate metrics
    if len(results) > 1:
        total_tp = sum(r.true_positives for r in results)
        total_fp = sum(r.false_positives for r in results)
        total_fn = sum(r.false_negatives for r in results)
        
        agg_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        agg_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        agg_f1 = 2 * agg_precision * agg_recall / (agg_precision + agg_recall) if (agg_precision + agg_recall) > 0 else 0
        
        print("\n" + "=" * 60)
        print("AGGREGATE METRICS")
        print("=" * 60)
        print(f"  Precision: {agg_precision:.1%}")
        print(f"  Recall:    {agg_recall:.1%}")
        print(f"  F1 Score:  {agg_f1:.1%}")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )
    
    parser = argparse.ArgumentParser(description="Run Flamboyance benchmark")
    parser.add_argument(
        "--app",
        type=str,
        help="Specific app to benchmark (default: all)",
    )
    parser.add_argument(
        "--tool",
        type=str,
        default="flamboyance",
        choices=["flamboyance", "devin"],
        help="Tool to benchmark",
    )
    parser.add_argument(
        "--skip-start",
        action="store_true",
        help="Skip starting the app (assume it's already running)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available apps",
    )
    
    args = parser.parse_args()
    
    # List available apps
    available_apps = [
        p.stem for p in GROUND_TRUTH_DIR.glob("*.json")
    ]
    
    if args.list:
        print("Available apps:")
        for app in available_apps:
            gt = load_ground_truth(app)
            print(f"  {app}: {len(gt.issues)} issues (port {gt.port})")
        return
    
    # Determine which apps to run
    if args.app:
        apps = [args.app]
    else:
        apps = available_apps
    
    if not apps:
        print("No apps found. Create ground truth files in benchmark/ground_truth/")
        return
    
    # Run benchmarks
    results = []
    for app in apps:
        log.info(f"Running benchmark for {app}...")
        try:
            result = await run_benchmark_for_app(
                app,
                tool=args.tool,
                skip_start=args.skip_start,
            )
            results.append(result)
        except Exception as e:
            log.error(f"Failed to benchmark {app}: {e}")
            continue
    
    if results:
        print_results(results)
        save_results(results)


if __name__ == "__main__":
    asyncio.run(main())
