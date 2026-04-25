/**
 * Lightweight HTTP client for the Flamboyance MCP server.
 *
 * Talks to the FastMCP server over HTTP (default: localhost:8765).
 * Each public method corresponds to one MCP tool.
 */

import * as http from "http";

interface AgentStatus {
  persona: string;
  status: string;
  currentUrl: string;
  frustrationEvents: string[];
  elapsedSeconds: number;
}

export class MCPClient {
  private baseUrl: string;

  constructor(baseUrl = "http://localhost:8765") {
    this.baseUrl = baseUrl;
  }

  async runSimulation(
    url: string,
    personas?: string[],
    mode?: string,
    timeout?: number
  ): Promise<string> {
    const result = await this.callTool("run_simulation", {
      url,
      personas: personas ?? ["frustrated_exec", "non_tech_senior", "power_user"],
      mode: mode ?? "local",
      timeout: timeout ?? 60,
    });
    return result.run_id;
  }

  async getLiveFeed(runId: string): Promise<AgentStatus[]> {
    const result = await this.callTool("get_live_feed", { run_id: runId });
    return result.agents;
  }

  async getReport(runId: string): Promise<string> {
    const result = await this.callTool("get_report", { run_id: runId });
    return result.markdown;
  }

  async stopSimulation(runId: string): Promise<boolean> {
    const result = await this.callTool("stop_simulation", { run_id: runId });
    return result.stopped;
  }

  dispose(): void {
    // nothing to clean up for HTTP client
  }

  private callTool(
    toolName: string,
    args: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify({
        jsonrpc: "2.0",
        method: "tools/call",
        params: { name: toolName, arguments: args },
        id: Date.now(),
      });

      const url = new URL(this.baseUrl);
      const options: http.RequestOptions = {
        hostname: url.hostname,
        port: url.port || 8765,
        path: "/mcp",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
      };

      const req = http.request(options, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            const json = JSON.parse(data);
            if (json.error) {
              reject(new Error(json.error.message ?? JSON.stringify(json.error)));
            } else {
              resolve(json.result ?? json);
            }
          } catch {
            reject(new Error(`Invalid JSON response: ${data.slice(0, 200)}`));
          }
        });
      });

      req.on("error", reject);
      req.write(payload);
      req.end();
    });
  }
}
