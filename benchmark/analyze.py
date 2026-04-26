"""Analysis script for benchmark results."""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

log = logging.getLogger(__name__)

BENCHMARK_DIR = Path(__file__).parent
RESULTS_DIR = BENCHMARK_DIR / "results"


def load_latest_results() -> dict | None:
    """Load the most recent benchmark results."""
    result_files = sorted(RESULTS_DIR.glob("benchmark-*.json"), reverse=True)
    if not result_files:
        return None
    
    with open(result_files[0]) as f:
        return json.load(f)


def load_all_results() -> list[dict]:
    """Load all benchmark results for trend analysis."""
    results = []
    for path in sorted(RESULTS_DIR.glob("benchmark-*.json")):
        with open(path) as f:
            results.append(json.load(f))
    return results


def analyze_by_tool(results: dict) -> dict:
    """Group results by tool and compute aggregate metrics."""
    by_tool = defaultdict(list)
    
    for r in results["results"]:
        by_tool[r["tool"]].append(r)
    
    aggregates = {}
    for tool, tool_results in by_tool.items():
        total_tp = sum(r["true_positives"] for r in tool_results)
        total_fp = sum(r["false_positives"] for r in tool_results)
        total_fn = sum(r["false_negatives"] for r in tool_results)
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        aggregates[tool] = {
            "apps": len(tool_results),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
        }
    
    return aggregates


def generate_markdown_report(results: dict) -> str:
    """Generate a markdown report from benchmark results."""
    lines = [
        "# Flamboyance Benchmark Results",
        "",
        f"**Timestamp:** {results['timestamp']}",
        "",
    ]
    
    # Aggregate by tool
    by_tool = analyze_by_tool(results)
    
    lines.append("## Summary by Tool")
    lines.append("")
    lines.append("| Tool | Apps | Precision | Recall | F1 | TP | FP | FN |")
    lines.append("|------|------|-----------|--------|----|----|----|----|")
    
    for tool, metrics in by_tool.items():
        lines.append(
            f"| {tool} | {metrics['apps']} | "
            f"{metrics['precision']:.1%} | {metrics['recall']:.1%} | {metrics['f1']:.1%} | "
            f"{metrics['true_positives']} | {metrics['false_positives']} | {metrics['false_negatives']} |"
        )
    
    lines.append("")
    lines.append("## Results by App")
    lines.append("")
    lines.append("| App | Tool | Precision | Recall | F1 | Detected | Ground Truth |")
    lines.append("|-----|------|-----------|--------|----|-----------| -------------|")
    
    for r in results["results"]:
        lines.append(
            f"| {r['app']} | {r['tool']} | "
            f"{r['precision']:.1%} | {r['recall']:.1%} | {r['f1']:.1%} | "
            f"{r['detected_count']} | {r['ground_truth_count']} |"
        )
    
    # Statistical comparison if both tools present
    if len(by_tool) >= 2 and "flamboyance" in by_tool and "devin" in by_tool:
        lines.append("")
        lines.append("## Flamboyance vs Devin Comparison")
        lines.append("")
        
        fl = by_tool["flamboyance"]
        dv = by_tool["devin"]
        
        precision_diff = fl["precision"] - dv["precision"]
        recall_diff = fl["recall"] - dv["recall"]
        f1_diff = fl["f1"] - dv["f1"]
        
        lines.append("| Metric | Flamboyance | Devin | Difference |")
        lines.append("|--------|-------------|-------|------------|")
        lines.append(f"| Precision | {fl['precision']:.1%} | {dv['precision']:.1%} | {precision_diff:+.1%} |")
        lines.append(f"| Recall | {fl['recall']:.1%} | {dv['recall']:.1%} | {recall_diff:+.1%} |")
        lines.append(f"| F1 Score | {fl['f1']:.1%} | {dv['f1']:.1%} | {f1_diff:+.1%} |")
        
        # Interpretation
        lines.append("")
        if f1_diff > 0.05:
            lines.append(f"**Flamboyance outperforms Devin by {f1_diff:.1%} F1 score.**")
        elif f1_diff < -0.05:
            lines.append(f"**Devin outperforms Flamboyance by {-f1_diff:.1%} F1 score.**")
        else:
            lines.append("**Performance is comparable between tools.**")
    
    return "\n".join(lines)


def mcnemar_test(results: dict) -> dict | None:
    """Perform McNemar's test for statistical significance.
    
    Compares paired predictions: cases where tools disagree.
    """
    # This requires matched predictions per issue, which we don't have
    # in the current results format. Return placeholder.
    return {
        "note": "McNemar's test requires per-issue matched predictions. "
                "Run benchmark with --detailed flag to enable."
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    
    parser = argparse.ArgumentParser(description="Analyze benchmark results")
    parser.add_argument(
        "--output",
        type=str,
        default=str(BENCHMARK_DIR / "RESULTS.md"),
        help="Output path for markdown report",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of markdown",
    )
    
    args = parser.parse_args()
    
    results = load_latest_results()
    if not results:
        print("No benchmark results found. Run: python -m benchmark.run_benchmark")
        return
    
    if args.json:
        analysis = {
            "timestamp": results["timestamp"],
            "by_tool": analyze_by_tool(results),
            "results": results["results"],
        }
        print(json.dumps(analysis, indent=2))
    else:
        report = generate_markdown_report(results)
        
        # Write to file
        output_path = Path(args.output)
        output_path.write_text(report)
        print(f"Report written to {output_path}")
        
        # Also print to console
        print("\n" + report)


if __name__ == "__main__":
    main()
