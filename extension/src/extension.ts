import * as vscode from "vscode";
import { SidebarProvider } from "./sidebar";
import { MCPClient } from "./mcpClient";

let mcpClient: MCPClient;

export function activate(context: vscode.ExtensionContext): void {
  mcpClient = new MCPClient();

  const sidebarProvider = new SidebarProvider(context.extensionUri, mcpClient);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      "flamboyance.sidebar",
      sidebarProvider
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("flamboyance.runSimulation", async () => {
      const url = await vscode.window.showInputBox({
        prompt: "Target URL to test for UX friction",
        value: "http://localhost:3000",
      });
      if (!url) {
        return;
      }

      const modeChoice = await vscode.window.showQuickPick(["local", "docker"], {
        placeHolder: "Execution mode",
      });
      if (!modeChoice) {
        return;
      }

      try {
        const runId = await mcpClient.runSimulation(url, undefined, modeChoice);
        sidebarProvider.postMessage({ type: "simulationStarted", runId });
        vscode.window.showInformationMessage(
          `Flamboyance simulation started: ${runId}`
        );
      } catch (err) {
        vscode.window.showErrorMessage(
          `Simulation failed: ${err instanceof Error ? err.message : String(err)}`
        );
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("flamboyance.stopSimulation", async () => {
      const runId = await vscode.window.showInputBox({
        prompt: "Run ID to stop",
      });
      if (!runId) {
        return;
      }
      try {
        await mcpClient.stopSimulation(runId);
        vscode.window.showInformationMessage(`Simulation ${runId} stopped.`);
      } catch (err) {
        vscode.window.showErrorMessage(
          `Stop failed: ${err instanceof Error ? err.message : String(err)}`
        );
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("flamboyance.showReport", async () => {
      const runId = await vscode.window.showInputBox({
        prompt: "Run ID for report",
      });
      if (!runId) {
        return;
      }
      try {
        const markdown = await mcpClient.getReport(runId);
        const doc = await vscode.workspace.openTextDocument({
          content: markdown,
          language: "markdown",
        });
        await vscode.window.showTextDocument(doc, { preview: true });
      } catch (err) {
        vscode.window.showErrorMessage(
          `Report failed: ${err instanceof Error ? err.message : String(err)}`
        );
      }
    })
  );
}

export function deactivate(): void {
  mcpClient?.dispose();
}
