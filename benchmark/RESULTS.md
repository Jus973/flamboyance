# Flamboyance Benchmark Results

*No benchmark results yet. Run `python -m benchmark.run_benchmark` to generate.*

## How to Run

```bash
# Run benchmark against all test apps
python -m benchmark.run_benchmark

# Run against a specific app
python -m benchmark.run_benchmark --app buggy-checkout

# Skip starting apps (if already running)
python -m benchmark.run_benchmark --skip-start

# Analyze results
python -m benchmark.analyze
```

## Test Apps

| App | Port | Issues | Description |
|-----|------|--------|-------------|
| buggy-checkout | 5180 | 8 | E-commerce checkout with broken flows |
| confusing-signup | 5181 | 12 | Multi-step registration with dead ends |

## Expected Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Recall | ≥70% | % of known issues detected |
| Precision | ≥80% | % of reported issues that are real |
| F1 Score | ≥75% | Harmonic mean of precision/recall |
