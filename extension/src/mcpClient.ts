/**
 * Dual-transport MCP client for the Flamboyance MCP server.
 *
 * Supports two transport modes:
 * - **stdio**: Spawns `python -m mcp.server` as a child process (default)
 * - **http**: Connects to a running MCP server over HTTP (fallback for Docker/remote)
 *
 * Each public method corresponds to one MCP tool.
 */

import * as http from "http";
import { ChildProcess } from "child_process";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

export interface AgentStatus {
  persona: string;
  status: string;
  currentUrl: string;
  frustrationEvents: string[];
  elapsedSeconds: number;
  llmCalls?: number;
  llmTokens?: number;
}

export type TransportType = "stdio" | "http";

export interface MCPClientOptions {
  transport: TransportType;
  pythonPath?: string;
  httpUrl?: string;
  workingDirectory?: string;
}

export interface IMCPClient {
  runSimulation(
    url: string,
    personas?: string[],
    mode?: string,
    timeout?: number,
    llmMode?: boolean
  ): Promise<string>;
  getLiveFeed(runId: string): Promise<AgentStatus[]>;
  getReport(runId: string): Promise<string>;
  stopSimulation(runId: string): Promise<boolean>;
  dispose(): void;
}

/**
 * Factory function to create the appropriate MCP client.
 */
export function createMCPClient(options: MCPClientOptions): IMCPClient {
  if (options.transport === "stdio") {
    return new StdioMCPClient(
      options.pythonPath ?? "python3",
      options.workingDirectory
    );
  }
  return new HttpMCPClient(options.httpUrl ?? "http://localhost:8765");
}

/**
 * Stdio transport client - spawns Python MCP server as child process.
 */
class StdioMCPClient implements IMCPClient {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;
  private process: ChildProcess | null = null;
  private pythonPath: string;
  private workingDirectory?: string;
  private initPromise: Promise<void> | null = null;

  constructor(pythonPath: string, workingDirectory?: string) {
    this.pythonPath = pythonPath;
    this.workingDirectory = workingDirectory;
  }

  private async ensureConnected(): Promise<Client> {
    if (this.client) {
      return this.client;
    }

    if (this.initPromise) {
      await this.initPromise;
      return this.client!;
    }

    this.initPromise = this.connect();
    await this.initPromise;
    return this.client!;
  }

  private async connect(): Promise<void> {
    this.transport = new StdioClientTransport({
      command: this.pythonPath,
      args: ["-m", "mcp.server"],
      cwd: this.workingDirectory,
    });

    this.client = new Client(
      { name: "flamboyance-extension", version: "0.1.0" },
      { capabilities: {} }
    );

    await this.client.connect(this.transport);
  }

  async runSimulation(
    url: string,
    personas?: string[],
    mode?: string,
    timeout?: number,
    llmMode?: boolean
  ): Promise<string> {
    const client = await this.ensureConnected();
    const result = await client.callTool({
      name: "run_simulation",
      arguments: {
        url,
        personas: personas ?? ["frustrated_exec", "non_tech_senior", "power_user"],
        mode: mode ?? "local",
        timeout: timeout ?? 60,
        llm_mode: llmMode ?? false,
      },
    });
    const content = result.content as Array<{ type: string; text?: string }>;
    const textContent = content.find((c) => c.type === "text");
    if (!textContent?.text) {
      throw new Error("No text content in response");
    }
    const parsed = JSON.parse(textContent.text);
    if (parsed.error) {
      throw new Error(parsed.error);
    }
    return parsed.run_id;
  }

  async getLiveFeed(runId: string): Promise<AgentStatus[]> {
    const client = await this.ensureConnected();
    const result = await client.callTool({
      name: "get_live_feed",
      arguments: { run_id: runId },
    });
    const content = result.content as Array<{ type: string; text?: string }>;
    const textContent = content.find((c) => c.type === "text");
    if (!textContent?.text) {
      throw new Error("No text content in response");
    }
    const parsed = JSON.parse(textContent.text);
    return parsed.agents as AgentStatus[];
  }

  async getReport(runId: string): Promise<string> {
    const client = await this.ensureConnected();
    const result = await client.callTool({
      name: "get_report",
      arguments: { run_id: runId },
    });
    const content = result.content as Array<{ type: string; text?: string }>;
    const textContent = content.find((c) => c.type === "text");
    if (!textContent?.text) {
      throw new Error("No text content in response");
    }
    const parsed = JSON.parse(textContent.text);
    return parsed.markdown as string;
  }

  async stopSimulation(runId: string): Promise<boolean> {
    const client = await this.ensureConnected();
    const result = await client.callTool({
      name: "stop_simulation",
      arguments: { run_id: runId },
    });
    const content = result.content as Array<{ type: string; text?: string }>;
    const textContent = content.find((c) => c.type === "text");
    if (!textContent?.text) {
      throw new Error("No text content in response");
    }
    const parsed = JSON.parse(textContent.text);
    return parsed.stopped as boolean;
  }

  dispose(): void {
    if (this.client) {
      this.client.close().catch(() => {});
      this.client = null;
    }
    if (this.transport) {
      this.transport.close().catch(() => {});
      this.transport = null;
    }
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
    this.initPromise = null;
  }
}

/**
 * HTTP transport client - connects to running MCP server.
 */
class HttpMCPClient implements IMCPClient {
  private baseUrl: string;

  constructor(baseUrl = "http://localhost:8765") {
    this.baseUrl = baseUrl;
  }

  async runSimulation(
    url: string,
    personas?: string[],
    mode?: string,
    timeout?: number,
    llmMode?: boolean
  ): Promise<string> {
    const result = await this.callTool("run_simulation", {
      url,
      personas: personas ?? ["frustrated_exec", "non_tech_senior", "power_user"],
      mode: mode ?? "local",
      timeout: timeout ?? 60,
      llm_mode: llmMode ?? false,
    });
    return result.run_id as string;
  }

  async getLiveFeed(runId: string): Promise<AgentStatus[]> {
    const result = await this.callTool("get_live_feed", { run_id: runId });
    return result.agents as AgentStatus[];
  }

  async getReport(runId: string): Promise<string> {
    const result = await this.callTool("get_report", { run_id: runId });
    return result.markdown as string;
  }

  async stopSimulation(runId: string): Promise<boolean> {
    const result = await this.callTool("stop_simulation", { run_id: runId });
    return result.stopped as boolean;
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

/**
 * Legacy export for backward compatibility.
 * @deprecated Use createMCPClient() instead.
 */
export class MCPClient extends HttpMCPClient {
  constructor(baseUrl = "http://localhost:8765") {
    super(baseUrl);
  }
}
