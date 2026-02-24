| Priority | Issue | Action | Fixed |
|----------|-------|--------|-------|
| **High** | Command injection via `num_commits` in `_run_git()` | Explicitly cast `num_commits = int(num_commits)` with bounds checking (1–100) | 2026-02-23 |
| **High** | Arbitrary file read via `rglob("*.yml")` traversing entire filesystem | Scope to `.github/workflows/` or `.gitlab-ci.yml` only, limit traversal depth | 2026-02-23 |
| **High** | `app_name` injected unsanitized into YAML/Groovy templates | Sanitize `app_name` to alphanumeric + hyphens only | 2026-02-23 |
| **Medium** | Linear API key passed without `Bearer` prefix, fragile auth pattern | Verify Linear's expected format; avoid leaking raw key in logs | SKIP FOR NOW: could break existing key, needs testing |
| **Medium** | No `origin` validation on `postMessage` (`"*"` target) | Validate `event.origin` on inbound messages in widget handler | SKIP FOR NOW: VS Code uses vscode-webview:// origins that vary, needs research |
| **Medium** | CSS injection via `ctx.styles.css.fonts` into `<style>` element | Sanitize or allowlist CSS properties from host context | SJIP FOR NOW: "safe CSS" research needed, host VS Code = low risk |
| **Low** | No rate limiting on Linear API calls — one request per issue ID | Batch the GraphQL query or cap the number of IDs validated | SKIP FOR NOW: needs design decisions (batch query format, cap) |
| **Low** | `workflow_name` user-controlled, injected into YAML `[{workflow_name}]` | Validate against a safe regex pattern (e.g. `[a-zA-Z0-9 _-]+`) | 2026-02-23 |
| **Low** | `load_dotenv()` runs unconditionally, may load unrelated .env | Document expected env vars; consider explicit path for .env loading | SKIP FOR NOW: changing to explicit path could break CWD-based .env, needs testing |
| **Info** | No auth on MCP server (stdio-based, local only) | By design — document that local access = full tool access | |
| **Info** | docs_context.md is a static snapshot (2026-02-22) | No SSRF risk, but content may drift from live docs | |
| **Info** | SKILL.md instructs LLM to offer git rebase / file writes | Commit messages could contain prompt injection; consider sanitizing tool output | |