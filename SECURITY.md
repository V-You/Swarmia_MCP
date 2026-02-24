| Priority | Issue | Action | Fixed |
|----------|-------|--------|-------|
| **1** | Command injection via `num_commits` in `_run_git()` | Explicitly cast `num_commits = int(num_commits)` with bounds checking (1–100) | 2026-02-23 |
| **1** | Arbitrary file read via `rglob("*.yml")` traversing entire filesystem | Scope to `.github/workflows/` or `.gitlab-ci.yml` only, limit traversal depth | 2026-02-23 |
| **1** | `app_name` injected unsanitized into YAML/Groovy templates | Sanitize `app_name` to alphanumeric + hyphens only | 2026-02-23 |
| **2** | Linear API key passed without `Bearer` prefix, fragile auth pattern | Verify Linear's expected format; avoid leaking raw key in logs | SKIP FOR NOW: could break existing key, needs testing |
| **2** | No `origin` validation on `postMessage` (`"*"` target) | Validate `event.origin` on inbound messages in widget handler | SKIP FOR NOW: VS Code uses vscode-webview:// origins that vary, needs research |
| **2** | CSS injection via `ctx.styles.css.fonts` into `<style>` element | Sanitize or allowlist CSS properties from host context | SKIP FOR NOW: "safe CSS" research needed, host VS Code = low risk |
| **3** | No rate limiting on Linear API calls - one request per issue ID | Batch the GraphQL query or cap the number of IDs validated | SKIP FOR NOW: needs design decisions (batch query format, cap) |
| **3** | `workflow_name` user-controlled, injected into YAML `[{workflow_name}]` | Validate against a safe regex pattern (e.g. `[a-zA-Z0-9 _-]+`) | 2026-02-23 |
| **3** | `load_dotenv()` runs unconditionally, may load unrelated .env | Document expected env vars; consider explicit path for .env loading | SKIP FOR NOW: changing to explicit path could break CWD-based .env, needs testing |
| **4** | No auth on MCP server (stdio-based, local only) | N/A | By design |
| **4** | docs_context.md is a static snapshot (2026-02-22) | Content may drift from live docs | No SSRF risk |
| **4** | SKILL.md instructs LLM to offer git rebase / file writes | Commit messages could contain prompt injection, consider sanitizing tool output | Out of scope |