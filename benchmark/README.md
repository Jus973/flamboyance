# Flamboyance Benchmark Suite

Reproducible benchmark measuring UX friction detection accuracy (precision/recall) against manually-annotated test apps.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run benchmark against all test apps
python -m benchmark.run_benchmark

# Analyze results
python -m benchmark.analyze
```

## Methodology

### Ground Truth

Each test app has a `ground_truth.json` file with manually annotated UX issues:

```json
{
  "app": "buggy-checkout",
  "issues": [
    {
      "id": "issue-001",
      "type": "dead_end",
      "severity": "critical",
      "url_pattern": "/checkout",
      "description": "Submit button does nothing"
    }
  ]
}
```

### Metrics

- **Precision**: % of reported issues that are real problems
- **Recall**: % of known issues that the tool detects  
- **F1 Score**: Harmonic mean of precision/recall

### Issue Matching

A detected issue matches a ground truth issue if:
1. Same `type` (e.g., `dead_end`, `slow_load`)
2. URL contains the `url_pattern`
3. Description similarity > 0.5 (fuzzy match)

## Test Apps

| App | Port | Issues | Description |
|-----|------|--------|-------------|
| `buggy-checkout` | 5180 | 8 | E-commerce checkout with broken flows |
| `confusing-signup` | 5181 | 7 | Multi-step registration with dead ends |
| `mobile-nightmare` | 5182 | 6 | Mobile UX issues |

## Comparing Tools

### Flamboyance

```bash
python -m benchmark.run_benchmark --tool flamboyance
```

### Devin (manual)

1. Start test app: `cd benchmark/apps/buggy-checkout && npm run dev`
2. Ask Devin: "Find UX issues in http://localhost:5180"
3. Save response to `benchmark/devin_outputs/buggy-checkout.md`
4. Run: `python -m benchmark.run_benchmark --tool devin`

## Results

See [RESULTS.md](./RESULTS.md) for latest benchmark results.
