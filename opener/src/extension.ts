import * as vscode from 'vscode';
import * as http from 'http';

const PORT = 60351;
const HOST = '127.0.0.1';

// CORS headers for cross-origin requests from Galaxy frontend
const CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
};

export function activate(context: vscode.ExtensionContext) {
    // Create the HTTP server
    const server = http.createServer(async (req, res) => {
        // Handle CORS preflight requests
        if (req.method === 'OPTIONS') {
            res.writeHead(200, CORS_HEADERS);
            res.end();
            return;
        }

        try {
            // We must construct a URL object to parse parameters easily.
            // req.url comes in as '/open?path=...'
            const url = new URL(req.url || '', `http://${req.headers.host}`);

            // 1. Check Endpoint
            if (url.pathname !== '/open') {
                res.writeHead(404, CORS_HEADERS);
                res.end('Not Found');
                return;
            }

            // 2. Extract Parameters
            const filePath = url.searchParams.get('path');
            const type = url.searchParams.get('type') || 'file'; // 'file', 'folder', or 'workspace'
            const newWindow = url.searchParams.get('new_window') === 'true';

            if (!filePath) {
                res.writeHead(400, CORS_HEADERS);
                res.end('Missing "path" parameter');
                return;
            }

            // 3. Create VS Code URI
            // vscode.Uri.file handles Windows paths (C:\...) and Unix paths (/home/...) automatically
            const uri = vscode.Uri.file(filePath);

            // 4. Handle the Request
            if (type === 'folder' || type === 'workspace') {
                // Open Folder or Workspace
                // This command WILL reload the window (web iframe)
                await vscode.commands.executeCommand('vscode.openFolder', uri, {
                    forceNewWindow: newWindow
                });
                res.writeHead(200, CORS_HEADERS);
                res.end(`Opened ${type}: ${filePath}`);
            } else {
                // Open File
                // This happens seamlessly without reloading
                const doc = await vscode.workspace.openTextDocument(uri);
                await vscode.window.showTextDocument(doc);
                res.writeHead(200, CORS_HEADERS);
                res.end(`Opened file: ${filePath}`);
            }
        } catch (err) {
            console.error('Error in code-server-control:', err);
            res.writeHead(500, CORS_HEADERS);
            res.end('Error: ' + (err instanceof Error ? err.message : 'Unknown error'));
        }
    });

    // Start listening
    server.listen(PORT, HOST, () => {
        console.log(`Control server listening on http://${HOST}:${PORT}`);
    });

    // Cleanup: Close server when extension is deactivated
    context.subscriptions.push({
        dispose: () => server.close()
    });
}

export function deactivate() {
    // Cleanup logic is handled in subscriptions above
}
