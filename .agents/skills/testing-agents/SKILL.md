# Testing UX-Friction Agent Event Detection

## Overview
The Flamboyance agents detect UX friction by navigating websites with Playwright-based synthetic personas. Testing verifies that the `EventDetector` correctly emits events when friction patterns are encountered.

## Devin Secrets Needed
No secrets required. All testing runs locally.

## Prerequisites
- `pip install -e ".[dev]"` (installs project + pytest)
- `playwright install chromium` (required for browser automation)

## Event Types

### Notice Tier
- **slow_load**: Page load > 3000ms (configurable via `SLOW_LOAD_THRESHOLD_MS`)
- **dead_end**: No clickable elements (`<a>`, `<button>`, `<input>`, `[role=button]`, etc.) found on page
- **long_dwell**: Agent stays on page > 10s without a successful click (configurable via `LONG_DWELL_THRESHOLD_S`)

### Frustration Tier
- **circular_navigation**: A -> B -> A URL pattern
- **rage_click**: >= 3 clicks on same non-interactive element within 1.5s
- **unmet_goal**: Agent's goal not reached before timeout

## Unit Tests
```bash
python -m pytest tests/ -v
```
Covers all event types in `tests/test_events.py`.

## End-to-End Testing with Fixture Server

The Playground fixture site is NOT included in this repo. For E2E testing, create a minimal Python HTTP server:

```python
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(4)  # Triggers slow_load (> 3s)
            self._respond("<html><body><a href='/'>Back</a></body></html>")
        elif self.path == "/empty":
            self._respond("<html><body><p>No links here</p></body></html>")  # Triggers dead_end
        elif self.path == "/stuck":
            # Overlay blocks clicks -> triggers long_dwell after ~10s of failed clicks
            self._respond('''<html><body>
                <div style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:9999;"></div>
                <button>Submit</button>
            </body></html>''')
        else:
            self._respond("<html><body><a href='/'>Home</a><button>Click</button></body></html>")

    def _respond(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

HTTPServer(("127.0.0.1", 8756), Handler).serve_forever()
```

Start the server, then run agents:

```bash
# Test slow_load (use power_user: patience=0.9 -> timeout 6000ms, enough for 4s delay)
python -m agents.agent --url http://127.0.0.1:8756/slow --persona power_user --timeout 30

# Test dead_end
python -m agents.agent --url http://127.0.0.1:8756/empty --persona power_user --timeout 15

# Test long_dwell (takes ~15-20s due to click timeouts)
python -m agents.agent --url http://127.0.0.1:8756/stuck --persona power_user --timeout 30

# Control: no Notice events expected
python -m agents.agent --url http://127.0.0.1:8756/fast --persona power_user --timeout 15
```

## Verification
- Agent output is JSON to stdout with `frustration_events` array
- Check for `"kind": "slow_load"`, `"kind": "dead_end"`, `"kind": "long_dwell"` in the events
- Control page should produce zero Notice-tier events (only `unmet_goal` is expected)
- `long_dwell` should NOT flood: events should be spaced ~10s+ apart (timer resets after each firing)

## Running All Personas via Runner
```bash
python -m agents.runner_local --url http://127.0.0.1:8756/slow --timeout 60
```
This runs all 8 built-in personas sequentially and generates a Markdown report in `reports/`.

## Persona Selection Tips
- Use `power_user` (patience=0.9) for slow_load tests — high patience means longer page load timeout
- Use `frustrated_exec` (patience=0.2) to test early give-up behavior
- Use `accessibility_user` (prefers_visible_text=True) to test icon-only button filtering
- Use `non_tech_senior` (tech_literacy=0.2) to test hidden menu skipping
- Use `mobile_commuter` (viewport=375x667) to test mobile viewport behavior

## Troubleshooting
- If `playwright` import fails: run `pip install playwright && playwright install chromium`
- Port 9876 might be intercepted by proxy on some VMs — use port 8756 instead
- The `long_dwell` test requires a page where clicks fail (overlay technique) — if the overlay doesn't block clicks, try `pointer-events: none` on the overlay div
