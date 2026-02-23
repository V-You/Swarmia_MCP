/**
 * MCP Apps Extension (SEP-1865) communication utilities.
 *
 * Handles the JSON-RPC 2.0 handshake and notification protocol
 * between the widget (View) and the VS Code host.
 */

let nextRequestId = 1;
const pendingRequests = new Map<
  number,
  { resolve: (v: unknown) => void; reject: (e: Error) => void }
>();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyRecord = Record<string, any>;

/** Send a JSON-RPC request and wait for the host's response. */
export function sendRequest(
  method: string,
  params?: AnyRecord
): Promise<AnyRecord> {
  const id = nextRequestId++;
  const request = { jsonrpc: "2.0" as const, id, method, params: params ?? {} };

  return new Promise((resolve, reject) => {
    pendingRequests.set(id, {
      resolve: resolve as (v: unknown) => void,
      reject,
    });
    window.parent.postMessage(request, "*");
  });
}

/** Send a JSON-RPC notification (fire-and-forget). */
export function sendNotification(method: string, params?: AnyRecord): void {
  window.parent.postMessage(
    { jsonrpc: "2.0", method, params: params ?? {} },
    "*"
  );
}

export interface HostContext {
  theme?: "light" | "dark";
  styles?: {
    variables?: Record<string, string | undefined>;
    css?: { fonts?: string };
  };
  displayMode?: string;
  containerDimensions?: AnyRecord;
}

export interface InitResult {
  hostContext?: HostContext;
  hostCapabilities?: AnyRecord;
  hostInfo?: AnyRecord;
}

/**
 * Run the SEP-1865 lifecycle:
 *  1. ui/initialize  →  receive McpUiInitializeResult
 *  2. ui/notifications/initialized
 *  3. listen for tool-input / tool-result / host-context-changed
 *
 * Returns a cleanup function to remove the message listener.
 */
export function initMcpApp(opts: {
  /** Called when structuredContent arrives (tool-result or tool-input). */
  onData: (data: AnyRecord) => void;
  /** Widget name for clientInfo. */
  name: string;
}): () => void {
  let hostContext: HostContext | null = null;

  // ---- message listener -----------------------------------------------
  const handler = (event: MessageEvent) => {
    const msg = event.data;
    if (!msg || msg.jsonrpc !== "2.0") return;

    // Response to one of our requests
    if (msg.id !== undefined && (msg.result !== undefined || msg.error)) {
      const pending = pendingRequests.get(msg.id);
      if (pending) {
        pendingRequests.delete(msg.id);
        if (msg.error) {
          pending.reject(new Error(msg.error.message ?? "Unknown error"));
        } else {
          pending.resolve(msg.result);
        }
      }
      return;
    }

    // Notifications from host
    if (msg.method) {
      switch (msg.method) {
        case "ui/notifications/tool-input":
          if (msg.params?.arguments) {
            // Tool arguments — some servers pass data here too
          }
          break;

        case "ui/notifications/tool-result":
          if (msg.params?.structuredContent) {
            opts.onData(msg.params.structuredContent);
          }
          break;

        case "ui/notifications/tool-input-partial":
          // Optional: streaming partial input
          break;

        case "ui/notifications/host-context-changed":
          if (msg.params) {
            hostContext = { ...hostContext, ...msg.params };
            applyHostContext(hostContext);
          }
          break;

        case "ui/resource-teardown":
          break;
      }
    }
  };

  window.addEventListener("message", handler);

  // ---- initialize handshake -------------------------------------------
  (async () => {
    try {
      const result = (await sendRequest("ui/initialize", {
        protocolVersion: "2025-06-18",
        capabilities: {},
        clientInfo: { name: opts.name, version: "1.0.0" },
      })) as InitResult;

      hostContext = result.hostContext ?? null;
      if (hostContext) applyHostContext(hostContext);

      sendNotification("ui/notifications/initialized");
    } catch {
      // Host may not support MCP Apps — widget still works in standalone mode
      console.warn("MCP Apps init failed — running standalone");
    }
  })();

  return () => window.removeEventListener("message", handler);
}

// ---- theme tokens -----------------------------------------------------

const LIGHT_TOKENS: Record<string, string> = {
  "--sw-fg": "#1a1a1a",
  "--sw-fg-muted": "#666",
  "--sw-fg-faint": "#888",
  "--sw-bg": "#ffffff",
  "--sw-bg-surface": "#f5f5f5",
  "--sw-bg-card": "#fafafa",
  "--sw-border": "#e5e5e5",
  "--sw-row-border": "#eee",
  "--sw-header-border": "#ddd",
  "--sw-progress-bg": "#e5e5e5",
};

const DARK_TOKENS: Record<string, string> = {
  "--sw-fg": "#e0e0e0",
  "--sw-fg-muted": "#a0a0a0",
  "--sw-fg-faint": "#888",
  "--sw-bg": "#1e1e1e",
  "--sw-bg-surface": "#2a2a2a",
  "--sw-bg-card": "#252525",
  "--sw-border": "#404040",
  "--sw-row-border": "#333",
  "--sw-header-border": "#444",
  "--sw-progress-bg": "#333",
};

function applyThemeTokens(theme: "light" | "dark") {
  const tokens = theme === "dark" ? DARK_TOKENS : LIGHT_TOKENS;
  const root = document.documentElement;
  for (const [key, value] of Object.entries(tokens)) {
    root.style.setProperty(key, value);
  }
}

/** Inject fallback tokens based on prefers-color-scheme before host context arrives. */
function injectFallbackTheme() {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyThemeTokens(prefersDark ? "dark" : "light");
}

// Apply fallback immediately so widgets have theme tokens on first render
injectFallbackTheme();

/** Apply host theme CSS variables. */
function applyHostContext(ctx: HostContext) {
  if (ctx.theme) {
    document.documentElement.style.colorScheme = ctx.theme;
    applyThemeTokens(ctx.theme);
  }
  if (ctx.styles?.variables) {
    const root = document.documentElement;
    for (const [key, value] of Object.entries(ctx.styles.variables)) {
      if (value) root.style.setProperty(key, value);
    }
  }
  if (ctx.styles?.css?.fonts) {
    const style = document.createElement("style");
    style.textContent = ctx.styles.css.fonts;
    document.head.appendChild(style);
  }
}
