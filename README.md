# Swarmia Docs MCP

**Active documentation for Swarmia &ndash; directly in your IDE**

[Static knowledge bases are dead](https://www.reddit.com/r/SaaS/comments/1q86tzp/the_concept_of_static_knowledge_bases_is_dying/). Developer tooling grows increasingly complex &ndash; and traditional KBs are not cutting it. **Today,** when developers face integration or troubleshooting issues with platforms like Swarmia, they are forced to break their workflow, context-switch to a web browser, click through documentation. This traditional "pull" model of support relies entirely on the developer to find generic instructions and translate them into their specific local environment. This process is **slow, inefficient, and highlights the need for documentation that converges with tooling.**

This project introduces a singular Skill, backed by a custom MCP Server. You shift gears: from static documentation to interactive workflow. **Invoke `/swarmia`** directly within your IDE. The MCP server actively assesses your local environment &ndash; git history, branch names, CI/CD configuration &ndash; and provides actionable solutions:

* **Check commit hygiene** &ndash; verify branches and commits contain issue tracker IDs, validate against Linear API
* **Scaffold deployment tracking** &ndash; detect your CI/CD framework and generate Swarmia webhook config
* **Answer Swarmia questions** &ndash; query bundled documentation contextually, no browser needed

## Example 1: 

I'm new. I'm unsure what to do. ``/swarmia`` tells me what's wrong and how to fix:

<kbd><img src="img/Screenshot_2026-02-22_195923.png" alt="Example 1: /swarmia tells me what to do" width="111px" /></kbd>

It works:

<kbd><img src="img/Screenshot_2026-02-22_201741.png" alt="Example 1: I do it and succeed" width="111px" /></kbd>

I have my doubts that my Linear API key is working correctly. Let's check:

<kbd><img src="img/Screenshot_2026-02-22_203609.png" alt="Is my API key ok? Yep, sure is." width="111px" /></kbd>


---

# Usage

### 1. Prerequisites

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Optional: add a Linear API key for full issue validation
echo 'LINEAR_API_KEY=lin_api_yourkey' > .env
```

### 2. Open the repo in VS Code

That's it. The included `.vscode/mcp.json` tells VS Code how to start the MCP server:

```json
{
  "servers": {
    "swarmia": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "server.py"]
    }
  }
}
```

When you invoke `/swarmia` in the chat panel, VS Code automatically spawns `uv run server.py` as a child process and connects to it over stdio. No manual server startup needed &mdash; `uv` resolves dependencies and creates an isolated environment on first run.

### 3. Use `/swarmia` in the chat

Type `/swarmia` followed by your question or request. The LLM routes your intent to the right tool.

### Manual testing (optional)

For debugging or testing outside VS Code, you can run the server directly:

```bash
uv run server.py
```

Or use MCP Inspector to call tools interactively:

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

### IDE Skills

Two skills route your intent to the right tools:

| Skill | Persona | When to use |
|---|---|---|
| `/swarmia` | Developer pair programmer | Troubleshooting, checking branch/commit hygiene, general Swarmia questions |
| `/swarmia-admin` | Infrastructure engineer | Setting up deployment pipelines, configuring DORA metrics, initial integration |

### Example interactions

**Check if your branch will be tracked by Swarmia:**
```
/swarmia Is my current branch going to be tracked properly?
```
> Agent checks your local git &mdash; notices `fix-bug` lacks an `ENG-` prefix &mdash; replies:
> *"Your branch is missing a Linear ID. Shall I rename it to `ENG-XXX-fix-bug`?"*

**Audit recent commits for issue keys:**
```
/swarmia Check my last 5 commits for Swarmia compliance
```
> Agent calls `check_swarmia_commit_hygiene` &mdash; scans commit messages for `ENG-\d+` patterns &mdash; flags any missing issue keys and offers to help fix them via interactive rebase.

**Set up DORA metrics / deployment tracking:**
```
/swarmia-admin Set up deployment tracking for this repository
```
> Agent calls `scaffold_swarmia_deployment` &mdash; detects GitHub Actions (or GitLab CI, Jenkins) &mdash; generates the exact webhook YAML and explains which secrets to add.

**Ask a Swarmia question without leaving the IDE:**
```
/swarmia How does Swarmia calculate Cycle Time?
```
> Agent queries bundled documentation and returns a concise answer (max 3 sentences) grounded in official Swarmia help center content.

**Check why work isn't showing up in Investment Balance:**
```
/swarmia Why isn't my current work showing up in the Investment Balance view?
```
> Agent chains tools: checks your git history for missing issue keys, then explains that Swarmia requires PR&ndash;issue linking to categorize work into investment categories.



---

# Video

include screencast

# Details

## Architecture

```
IDE (VS Code)
  ├── /swarmia          (Skill — developer persona)
  ├── /swarmia-admin    (Skill — infra persona)
  └── LLM routes intent
        ↓
  server.py (FastMCP, stdio transport)
    ├── check_swarmia_commit_hygiene  →  local git + Linear GraphQL API
    ├── scaffold_swarmia_deployment   →  filesystem scan + YAML generation
    └── query_swarmia_docs            →  bundled docs_context.md
```

**Transport:** stdio (zero-latency local process). The server runs as a child process of the IDE &mdash; no network ports, no Docker.

**Distribution:** `pyproject.toml` + `uv`. One command (`uv run server.py`) handles everything.

## Tools

### `check_swarmia_commit_hygiene`
Reads local `git log` and `git branch`, regex-scans for issue tracker IDs (e.g. `ENG-123`), and optionally validates each issue against the Linear GraphQL API.

- **With `LINEAR_API_KEY`:** Full validation &mdash; fetches issue title, status, and confirms assignment to the current user
- **Without `LINEAR_API_KEY`:** Graceful degradation to regex-only matching with a note to add the key

### `scaffold_swarmia_deployment`
Detects the CI/CD framework (GitHub Actions, GitLab CI, Jenkins) by scanning the workspace, then generates the exact webhook configuration for Swarmia's Deployment API (`POST https://hook.swarmia.com/deployments`).

- Pure generation &mdash; returns YAML/config as text, never writes to the filesystem
- The IDE's native file-edit tools handle applying the diff

### `query_swarmia_docs`
Reads the bundled `docs_context.md` (curated from the Swarmia help center) and returns it with the user's query for the LLM to extract a concise answer.

Covers: getting started, deployment tracking, DORA metrics, cycle time, investment balance, PR&ndash;issue linking, working agreements.

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `LINEAR_API_KEY` | No (recommended) | Enables full Linear issue validation in commit hygiene checks |
| `SWARMIA_DEPLOYMENTS_AUTHORIZATION` | No | Referenced in generated CI/CD config snippets |

## Project Structure

```
├── server.py                           # MCP server (all 3 tools)
├── docs_context.md                     # Bundled Swarmia documentation
├── pyproject.toml                      # Dependencies & project metadata
├── .env                                # API keys (gitignored)
├── .vscode/
│   └── mcp.json                        # MCP server config (VS Code auto-starts)
├── .github/
│   ├── copilot_instructions.md         # Developer instructions for this repo
│   └── skills/
│       ├── swarmia/SKILL.md            # /swarmia skill definition
│       └── swarmia-admin/SKILL.md      # /swarmia-admin skill definition
└── README.md
```