import * as vscode from "vscode";
import { MCPClient } from "./mcpClient";

export class SidebarProvider implements vscode.WebviewViewProvider {
  private view?: vscode.WebviewView;
  private pollTimer?: ReturnType<typeof setInterval>;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly mcp: MCPClient
  ) {}

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ): void {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtml(webviewView.webview);

    webviewView.webview.onDidReceiveMessage(async (msg) => {
      switch (msg.type) {
        case "runSimulation": {
          try {
            const runId = await this.mcp.runSimulation(
              msg.url,
              msg.personas,
              msg.mode,
              msg.timeout
            );
            this.postMessage({ type: "simulationStarted", runId });
            this.startPolling(runId);
          } catch (err) {
            this.postMessage({
              type: "error",
              message: err instanceof Error ? err.message : String(err),
            });
          }
          break;
        }
        case "stopSimulation": {
          try {
            await this.mcp.stopSimulation(msg.runId);
            this.stopPolling();
            this.postMessage({ type: "simulationStopped", runId: msg.runId });
          } catch (err) {
            this.postMessage({
              type: "error",
              message: err instanceof Error ? err.message : String(err),
            });
          }
          break;
        }
        case "getReport": {
          try {
            const markdown = await this.mcp.getReport(msg.runId);
            this.postMessage({ type: "report", runId: msg.runId, markdown });
          } catch (err) {
            this.postMessage({
              type: "error",
              message: err instanceof Error ? err.message : String(err),
            });
          }
          break;
        }
      }
    });
  }

  postMessage(message: Record<string, unknown>): void {
    this.view?.webview.postMessage(message);
  }

  private startPolling(runId: string): void {
    this.stopPolling();
    this.pollTimer = setInterval(async () => {
      try {
        const agents = await this.mcp.getLiveFeed(runId);
        this.postMessage({ type: "liveFeed", runId, agents });
      } catch {
        // server may not be ready yet — silently retry
      }
    }, 2000);
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = undefined;
    }
  }

  private getHtml(_webview: vscode.Webview): string {
    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Flamboyance</title>
  <style>
    :root {
      --bg: var(--vscode-sideBar-background, #1e1e1e);
      --fg: var(--vscode-sideBar-foreground, #cccccc);
      --input-bg: var(--vscode-input-background, #3c3c3c);
      --input-fg: var(--vscode-input-foreground, #cccccc);
      --input-border: var(--vscode-input-border, #3c3c3c);
      --btn-bg: var(--vscode-button-background, #0e639c);
      --btn-fg: var(--vscode-button-foreground, #ffffff);
      --btn-hover: var(--vscode-button-hoverBackground, #1177bb);
      --badge-bg: var(--vscode-badge-background, #4d4d4d);
      --badge-fg: var(--vscode-badge-foreground, #ffffff);
      --error: var(--vscode-errorForeground, #f48771);
      --warning: #e8a317;
      --success: #89d185;
      --border: var(--vscode-panel-border, #2d2d2d);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--vscode-font-family, system-ui, sans-serif);
      font-size: var(--vscode-font-size, 13px);
      background: var(--bg);
      color: var(--fg);
      padding: 12px;
    }

    h2 { font-size: 14px; margin-bottom: 8px; }
    h3 { font-size: 13px; margin: 12px 0 6px; }

    .form-group { margin-bottom: 10px; }
    .form-group label { display: block; margin-bottom: 4px; font-weight: 600; }
    .form-group input, .form-group select {
      width: 100%;
      padding: 5px 8px;
      background: var(--input-bg);
      color: var(--input-fg);
      border: 1px solid var(--input-border);
      border-radius: 3px;
      font-size: 13px;
    }

    .btn {
      display: inline-block;
      padding: 6px 14px;
      background: var(--btn-bg);
      color: var(--btn-fg);
      border: none;
      border-radius: 3px;
      cursor: pointer;
      font-size: 13px;
      margin-right: 6px;
      margin-top: 4px;
    }
    .btn:hover { background: var(--btn-hover); }
    .btn.danger { background: var(--error); }

    .agent-card {
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 8px;
      margin-bottom: 8px;
    }
    .agent-card .name { font-weight: 600; }
    .agent-card .status { font-size: 12px; color: var(--badge-fg); }

    .badge {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge.running { background: var(--btn-bg); color: var(--btn-fg); }
    .badge.done    { background: var(--success); color: #000; }
    .badge.error   { background: var(--error); color: #000; }

    .event { color: var(--warning); font-size: 12px; margin-top: 2px; }
    .error-msg { color: var(--error); margin-top: 8px; }

    #report-section { margin-top: 12px; white-space: pre-wrap; font-size: 12px; }
    #feed-section .empty { color: var(--badge-bg); font-style: italic; }
  </style>
</head>
<body>
  <h2>Flamboyance UX Friction Monitor</h2>

  <div id="config-section">
    <div class="form-group">
      <label for="url-input">Target URL</label>
      <input id="url-input" type="text" value="http://localhost:3000" />
    </div>
    <div class="form-group">
      <label for="mode-select">Mode</label>
      <select id="mode-select">
        <option value="local">Local (sequential)</option>
        <option value="docker">Docker (parallel)</option>
      </select>
    </div>
    <div class="form-group">
      <label for="timeout-input">Timeout (s)</label>
      <input id="timeout-input" type="number" value="60" min="10" max="600" />
    </div>
    <button class="btn" id="run-btn">Run Simulation</button>
  </div>

  <div id="active-section" style="display:none;">
    <h3>Run: <span id="run-id-label"></span></h3>
    <button class="btn danger" id="stop-btn">Stop</button>
    <button class="btn" id="report-btn">Get Report</button>
  </div>

  <div id="feed-section">
    <h3>Live Feed</h3>
    <div id="feed-container"><span class="empty">No active simulation.</span></div>
  </div>

  <div id="report-section"></div>
  <div id="error-container"></div>

  <script>
    const vscode = acquireVsCodeApi();

    const runBtn     = document.getElementById('run-btn');
    const stopBtn    = document.getElementById('stop-btn');
    const reportBtn  = document.getElementById('report-btn');
    const urlInput   = document.getElementById('url-input');
    const modeSelect = document.getElementById('mode-select');
    const timeoutInput = document.getElementById('timeout-input');
    const runIdLabel = document.getElementById('run-id-label');
    const feedContainer = document.getElementById('feed-container');
    const reportSection = document.getElementById('report-section');
    const errorContainer = document.getElementById('error-container');
    const activeSection = document.getElementById('active-section');

    let currentRunId = null;

    runBtn.addEventListener('click', () => {
      vscode.postMessage({
        type: 'runSimulation',
        url: urlInput.value,
        mode: modeSelect.value,
        timeout: parseInt(timeoutInput.value, 10),
        personas: ['frustrated_exec', 'non_tech_senior', 'power_user'],
      });
      runBtn.disabled = true;
    });

    stopBtn.addEventListener('click', () => {
      if (currentRunId) {
        vscode.postMessage({ type: 'stopSimulation', runId: currentRunId });
      }
    });

    reportBtn.addEventListener('click', () => {
      if (currentRunId) {
        vscode.postMessage({ type: 'getReport', runId: currentRunId });
      }
    });

    window.addEventListener('message', (event) => {
      const msg = event.data;
      switch (msg.type) {
        case 'simulationStarted':
          currentRunId = msg.runId;
          runIdLabel.textContent = msg.runId;
          activeSection.style.display = 'block';
          runBtn.disabled = false;
          errorContainer.textContent = '';
          reportSection.textContent = '';
          break;

        case 'simulationStopped':
          activeSection.style.display = 'none';
          currentRunId = null;
          feedContainer.innerHTML = '<span class="empty">Simulation stopped.</span>';
          break;

        case 'liveFeed':
          renderFeed(msg.agents || []);
          break;

        case 'report':
          reportSection.textContent = msg.markdown || 'No report data.';
          break;

        case 'error':
          errorContainer.innerHTML = '<div class="error-msg">' +
            escapeHtml(msg.message) + '</div>';
          runBtn.disabled = false;
          break;
      }
    });

    function renderFeed(agents) {
      if (!agents.length) {
        feedContainer.innerHTML = '<span class="empty">Waiting for agents...</span>';
        return;
      }
      feedContainer.innerHTML = agents.map(a => {
        const badgeClass = a.status === 'running' ? 'running'
          : a.status === 'done' ? 'done' : 'error';
        const events = (a.frustrationEvents || [])
          .map(e => '<div class="event">' + escapeHtml(e) + '</div>')
          .join('');
        return '<div class="agent-card">' +
          '<span class="name">' + escapeHtml(a.persona) + '</span> ' +
          '<span class="badge ' + badgeClass + '">' + escapeHtml(a.status) + '</span>' +
          '<div class="status">URL: ' + escapeHtml(a.currentUrl || '—') +
          ' | ' + (a.elapsedSeconds || 0).toFixed(1) + 's</div>' +
          events + '</div>';
      }).join('');
    }

    function escapeHtml(s) {
      const d = document.createElement('div');
      d.textContent = s;
      return d.innerHTML;
    }
  </script>
</body>
</html>`;
  }
}
