"""
Swarmia MCP Server

A local MCP server that acts as an intelligent pair programmer for Swarmia integration.
Tools: check_swarmia_commit_hygiene, scaffold_swarmia_deployment, query_swarmia_docs

Run: uv run python -m swarmia_mcp
Test: npx @modelcontextprotocol/inspector uv run python -m swarmia_mcp
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import logging
import sys

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.apps import AppConfig
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

# Plain logger — avoids Rich column padding and line wrapping in VS Code
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(message)s"))
logger = logging.getLogger("swarmia_mcp")
logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Suppress FastMCP's Rich-formatted internal logger (causes line wrapping in VS Code)
logging.getLogger("fastmcp").setLevel(logging.WARNING)

load_dotenv()

# ---------------------------------------------------------------------------
# Widget HTML (built by Vite into assets/)
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent.parent / "assets"


def _load_widget_html(widget_name: str) -> str:
    """Load a built widget HTML file, inlining the JS bundle for self-contained serving."""
    html_path = ASSETS_DIR / widget_name / "index.html"
    if not html_path.exists():
        return f"<html><body><p>Widget '{widget_name}' not built. Run <code>pnpm run build</code>.</p></body></html>"

    html = html_path.read_text(encoding="utf-8")

    # Inline the JS bundle so the HTML is fully self-contained
    # Vite outputs: <script type="module" crossorigin src="../shared/xxx.js"></script>
    import re as _re

    def _inline_script(match: _re.Match) -> str:
        src = match.group(1)
        js_path = (html_path.parent / src).resolve()
        if js_path.exists():
            js_content = js_path.read_text(encoding="utf-8")
            return f'<script type="module">{js_content}</script>'
        return match.group(0)

    html = _re.sub(
        r'<script type="module" crossorigin src="([^"]+)"></script>',
        _inline_script,
        html,
    )
    return html

mcp = FastMCP(
    "Swarmia",
    instructions=(
        "You are a Swarmia integration assistant. Use these tools to help developers "
        "keep their code tracked in Swarmia, set up deployment pipelines, and answer "
        "questions about Swarmia — all without leaving the IDE."
    ),
)

LINEAR_API_URL = "https://api.linear.app/graphql"
ISSUE_KEY_PATTERN = re.compile(r"[A-Z]{2,10}-\d+")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_git(*args: str) -> str:
    """Run a git command and return stdout. Raises RuntimeError on failure."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {args[0]} failed")
    return result.stdout.strip()


def _linear_headers() -> dict[str, str] | None:
    key = os.getenv("LINEAR_API_KEY")
    if not key:
        return None
    return {"Authorization": key, "Content-Type": "application/json"}


def _query_linear_issues(issue_ids: list[str]) -> dict:
    """Query Linear GraphQL API for issue details. Returns {id: {title, state, assignee_id}}."""
    headers = _linear_headers()
    if not headers:
        return {}

    results: dict = {}
    # Batch: fetch each issue by identifier
    for issue_id in issue_ids:
        query = """
        query($filter: IssueFilter) {
            issues(filter: $filter, first: 1) {
                nodes {
                    identifier
                    title
                    state { name }
                    assignee { id }
                }
            }
        }
        """
        variables = {"filter": {"number": {"eq": int(issue_id.split("-")[1])}, "team": {"key": {"eq": issue_id.split("-")[0]}}}}
        try:
            resp = httpx.post(
                LINEAR_API_URL,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            nodes = data.get("data", {}).get("issues", {}).get("nodes", [])
            if nodes:
                node = nodes[0]
                results[issue_id] = {
                    "title": node.get("title", ""),
                    "state": node.get("state", {}).get("name", ""),
                    "assignee_id": (node.get("assignee") or {}).get("id"),
                }
        except (httpx.HTTPStatusError, httpx.RequestError):
            # Will be handled in caller — missing entries = unverified
            pass

    return results


def _get_linear_viewer_id() -> str | None:
    """Get the authenticated user's Linear ID."""
    headers = _linear_headers()
    if not headers:
        return None
    try:
        resp = httpx.post(
            LINEAR_API_URL,
            json={"query": "{ viewer { id } }"},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("viewer", {}).get("id")
    except (httpx.HTTPStatusError, httpx.RequestError):
        return None


# ---------------------------------------------------------------------------
# Tool 1: check_swarmia_commit_hygiene
# ---------------------------------------------------------------------------


@mcp.resource("ui://swarmia/commit-hygiene.html")
def commit_hygiene_view() -> str:
    """Interactive commit hygiene dashboard widget."""
    return _load_widget_html("commit-hygiene")


@mcp.tool(app=AppConfig(resource_uri="ui://swarmia/commit-hygiene.html"))
def check_swarmia_commit_hygiene(num_commits: int = 10) -> str:
    """Check if recent commits and the current branch follow Swarmia tracking conventions.

    Verifies that branch names and commit messages contain issue tracker IDs
    (e.g. ENG-123). If a LINEAR_API_KEY is configured, validates each issue
    against the Linear API to confirm it exists and is assigned to the current user.

    Args:
        num_commits: Number of recent commits to check (default: 10).
    """
    logger.info("check_swarmia_commit_hygiene: scanning last %d commits", num_commits)
    lines: list[str] = []

    # --- Get branch name ---
    try:
        branch = _run_git("branch", "--show-current")
    except RuntimeError:
        return (
            "Error: This directory is not a git repository or git is not installed. "
            "Please run this from a git-initialized project."
        )

    if not branch:
        branch = "(detached HEAD)"

    branch_ids = ISSUE_KEY_PATTERN.findall(branch)
    lines.append(f"**Current branch:** `{branch}`")
    if branch_ids:
        lines.append(f"  ✅ Issue key(s) found in branch name: {', '.join(branch_ids)}")
    else:
        lines.append(
            "  ⚠️ No issue key found in branch name. "
            "Swarmia tracks work by linking branches to issue IDs (e.g. `ENG-123-fix-auth`). "
            "Consider renaming: `git branch -m <ENG-XXX>-{current-name}`"
        )

    # --- Get commits ---
    try:
        log_output = _run_git("log", f"-n{num_commits}", "--oneline")
    except RuntimeError:
        lines.append("\n⚠️ No commits found in this repository yet.")
        return "\n".join(lines)

    if not log_output:
        lines.append("\n⚠️ No commits found in this repository yet.")
        return "\n".join(lines)

    commits = []
    for line in log_output.splitlines():
        parts = line.split(" ", 1)
        sha = parts[0]
        message = parts[1] if len(parts) > 1 else ""
        ids_found = ISSUE_KEY_PATTERN.findall(message)
        commits.append({"sha": sha, "message": message, "ids": ids_found})

    # --- Collect all unique issue IDs ---
    all_ids = set()
    for c in commits:
        all_ids.update(c["ids"])
    all_ids.update(branch_ids)

    # --- Linear validation (if key available) ---
    linear_available = bool(os.getenv("LINEAR_API_KEY"))
    linear_data: dict = {}
    viewer_id: str | None = None

    if linear_available and all_ids:
        viewer_id = _get_linear_viewer_id()
        linear_data = _query_linear_issues(list(all_ids))
        if not linear_data and not viewer_id:
            lines.append(
                "\n⚠️ LINEAR_API_KEY is set but the Linear API returned no data. "
                "The key may be invalid. Falling back to regex-only validation."
            )
            linear_available = False

    # --- Format commit results ---
    lines.append(f"\n**Last {len(commits)} commits:**")
    for c in commits:
        status = "✅" if c["ids"] else "⚠️"
        id_str = ", ".join(c["ids"]) if c["ids"] else "no issue key"
        lines.append(f"  {status} `{c['sha']}` {c['message']} [{id_str}]")

    # --- Linear details ---
    if linear_available and linear_data:
        lines.append("\n**Linear issue verification:**")
        for issue_id, info in linear_data.items():
            assignee_match = ""
            if viewer_id and info.get("assignee_id"):
                if info["assignee_id"] == viewer_id:
                    assignee_match = " (assigned to you ✅)"
                else:
                    assignee_match = " (⚠️ assigned to someone else)"
            elif viewer_id and not info.get("assignee_id"):
                assignee_match = " (unassigned)"
            lines.append(
                f"  • **{issue_id}**: {info['title']} — *{info['state']}*{assignee_match}"
            )

        unverified = all_ids - set(linear_data.keys())
        if unverified:
            lines.append(
                f"\n  ⚠️ Could not verify: {', '.join(sorted(unverified))}. "
                "These may belong to a different team or workspace."
            )
    elif not linear_available and all_ids:
        lines.append(
            "\n*Regex validation passed. Add LINEAR_API_KEY to .env to verify "
            "issue status directly against your tracker.*"
        )

    # --- Summary ---
    missing = [c for c in commits if not c["ids"]]
    if missing:
        lines.append(
            f"\n**Summary:** {len(missing)}/{len(commits)} commits are missing issue keys. "
            "These commits won't be tracked by Swarmia."
        )
    else:
        lines.append(f"\n**Summary:** All {len(commits)} commits have issue keys. ✅")

    # Build structured data for the widget
    widget_linear = {}
    for issue_id, info in linear_data.items():
        assigned_to_you = None
        if viewer_id and info.get("assignee_id"):
            assigned_to_you = info["assignee_id"] == viewer_id
        widget_linear[issue_id] = {
            "title": info["title"],
            "state": info["state"],
            "assigned_to_you": assigned_to_you,
        }

    return ToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
        structured_content={
            "branch": branch,
            "branch_ids": branch_ids,
            "commits": commits,
            "linear_data": widget_linear,
            "summary": lines[-1] if lines else "",
        },
        meta={},
    )


# ---------------------------------------------------------------------------
# Tool 2: scaffold_swarmia_deployment
# ---------------------------------------------------------------------------

GITHUB_ACTIONS_TEMPLATE = """\
# Swarmia Deployment Tracking
# Add SWARMIA_DEPLOYMENTS_AUTHORIZATION to your repository secrets
# Docs: https://help.swarmia.com/deployment-tracking

name: Swarmia Deployment Tracking

on:
  workflow_run:
    workflows: [{workflow_name}]
    types: [completed]

jobs:
  swarmia-deployment:
    if: ${{{{ github.event.workflow_run.conclusion == 'success' }}}}
    runs-on: ubuntu-latest
    steps:
      - name: Notify Swarmia
        run: |
          curl -X POST https://hook.swarmia.com/deployments \\
            -H "Authorization: ${{{{ secrets.SWARMIA_DEPLOYMENTS_AUTHORIZATION }}}}" \\
            -H "Content-Type: application/json" \\
            -d '{{
              "version": "${{{{ github.event.workflow_run.head_sha }}}}",
              "appName": "{app_name}",
              "commitSha": "${{{{ github.event.workflow_run.head_sha }}}}",
              "repositoryFullName": "${{{{ github.repository }}}}"
            }}'
"""

@mcp.resource("ui://swarmia/deployment-scaffold.html")
def deployment_scaffold_view() -> str:
    """Interactive deployment scaffold configuration wizard."""
    return _load_widget_html("deployment-scaffold")


GITLAB_CI_TEMPLATE = """\
# Swarmia Deployment Tracking
# Add SWARMIA_DEPLOYMENTS_AUTHORIZATION as a CI/CD variable
# Docs: https://help.swarmia.com/deployment-tracking

swarmia-deployment:
  stage: .post
  script:
    - |
      curl -X POST https://hook.swarmia.com/deployments \\
        -H "Authorization: $SWARMIA_DEPLOYMENTS_AUTHORIZATION" \\
        -H "Content-Type: application/json" \\
        -d '{{
          "version": "$CI_COMMIT_SHA",
          "appName": "{app_name}",
          "commitSha": "$CI_COMMIT_SHA",
          "repositoryFullName": "$CI_PROJECT_PATH"
        }}'
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
"""


@mcp.tool(app=AppConfig(resource_uri="ui://swarmia/deployment-scaffold.html"))
def scaffold_swarmia_deployment(
    app_name: str = "",
    workflow_name: str = "deploy",
) -> str:
    """Generate CI/CD configuration for Swarmia's Deployment Tracking webhook.

    Detects the CI/CD framework in the current repository and produces the
    exact YAML snippet needed to notify Swarmia of deployments. The generated
    config sends a POST to https://hook.swarmia.com/deployments with the
    required fields: version, appName, commitSha, repositoryFullName.

    This tool does NOT write files — it returns the YAML as text. The IDE's
    native file-edit capabilities should be used to apply it.

    Args:
        app_name: The application/service name for Swarmia tracking.
                  Defaults to the repository directory name.
        workflow_name: For GitHub Actions, the name of the deployment workflow
                       to trigger on (default: "deploy").
    """
    logger.info("scaffold_swarmia_deployment: generating config (app=%s)", app_name or "<auto>")
    workspace = Path.cwd()

    if not app_name:
        app_name = workspace.name

    # Detect CI/CD framework
    has_github = (workspace / ".github" / "workflows").is_dir()
    has_gitlab = (workspace / ".gitlab-ci.yml").is_file()
    has_jenkins = (workspace / "Jenkinsfile").is_file()

    lines: list[str] = []

    if has_github:
        lines.append("**Detected CI/CD:** GitHub Actions\n")
        lines.append(
            "Add this as a new workflow file (e.g. `.github/workflows/swarmia-deploy.yml`):\n"
        )
        lines.append("```yaml")
        lines.append(
            GITHUB_ACTIONS_TEMPLATE.format(
                app_name=app_name, workflow_name=workflow_name
            )
        )
        lines.append("```")
        lines.append(
            "\n**Setup steps:**\n"
            "1. Add `SWARMIA_DEPLOYMENTS_AUTHORIZATION` to your GitHub repository secrets "
            "(Settings → Secrets and variables → Actions)\n"
            f'2. Verify the `workflow_name` matches your deploy workflow (currently: `"{workflow_name}"`)\n'
            "3. Commit and push this workflow file"
        )
    elif has_gitlab:
        lines.append("**Detected CI/CD:** GitLab CI\n")
        lines.append("Add this job to your `.gitlab-ci.yml`:\n")
        lines.append("```yaml")
        lines.append(GITLAB_CI_TEMPLATE.format(app_name=app_name))
        lines.append("```")
        lines.append(
            "\n**Setup steps:**\n"
            "1. Add `SWARMIA_DEPLOYMENTS_AUTHORIZATION` as a CI/CD variable "
            "(Settings → CI/CD → Variables)\n"
            "2. Commit and push the updated `.gitlab-ci.yml`"
        )
    elif has_jenkins:
        lines.append(
            "**Detected CI/CD:** Jenkins (Jenkinsfile found)\n\n"
            "Swarmia's deployment webhook is a simple HTTP POST. Add this stage "
            "to your Jenkinsfile after your deployment step:\n"
        )
        lines.append("```groovy")
        lines.append(
            f"""\
stage('Notify Swarmia') {{
    steps {{
        sh '''
            curl -X POST https://hook.swarmia.com/deployments \\
              -H "Authorization: $SWARMIA_DEPLOYMENTS_AUTHORIZATION" \\
              -H "Content-Type: application/json" \\
              -d '{{
                "version": "'$GIT_COMMIT'",
                "appName": "{app_name}",
                "commitSha": "'$GIT_COMMIT'",
                "repositoryFullName": "'$GIT_URL'"
              }}'
        '''
    }}
}}"""
        )
        lines.append("```")
        lines.append(
            "\n**Setup steps:**\n"
            "1. Add `SWARMIA_DEPLOYMENTS_AUTHORIZATION` as a Jenkins credential\n"
            "2. Inject it as an environment variable in your pipeline"
        )
    else:
        lines.append(
            "No `.github/workflows/`, `.gitlab-ci.yml`, or `Jenkinsfile` found in this repository.\n\n"
            "Swarmia deployment tracking requires a CI/CD pipeline that sends an HTTP POST "
            "to `https://hook.swarmia.com/deployments` after each successful deployment.\n\n"
            "**Required payload:**\n"
            "```json\n"
            "{\n"
            f'  "version": "<commit-sha>",\n'
            f'  "appName": "{app_name}",\n'
            f'  "commitSha": "<commit-sha>",\n'
            f'  "repositoryFullName": "<owner>/<repo>"\n'
            "}\n"
            "```\n\n"
            "**Header:** `Authorization: <SWARMIA_DEPLOYMENTS_AUTHORIZATION>`\n\n"
            "Would you like me to create a `.github/workflows/` directory and generate a GitHub Actions workflow?"
        )

    text = "\n".join(lines)

    # Detect which CI was found for the widget
    detected_ci = None
    if has_github:
        detected_ci = "GitHub Actions"
    elif has_gitlab:
        detected_ci = "GitLab CI"
    elif has_jenkins:
        detected_ci = "Jenkins"

    # Extract the raw YAML/config snippet (between code fences) for widget preview
    yaml_snippet = ""
    setup_steps: list[str] = []
    in_code = False
    code_lines: list[str] = []
    for line in lines:
        if line.startswith("```") and not in_code:
            in_code = True
            continue
        if line.startswith("```") and in_code:
            in_code = False
            continue
        if in_code:
            code_lines.append(line)
    yaml_snippet = "\n".join(code_lines)

    # Extract setup steps (lines starting with a number after **Setup steps:**)
    in_steps = False
    for line in lines:
        if "Setup steps:" in line:
            in_steps = True
            continue
        if in_steps and line.strip():
            # Strip leading number + dot
            step = line.strip()
            if step and step[0].isdigit():
                step = step.split(". ", 1)[-1]
            setup_steps.append(step)

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content={
            "detected_ci": detected_ci,
            "app_name": app_name,
            "workflow_name": workflow_name,
            "yaml_snippet": yaml_snippet,
            "setup_steps": setup_steps,
        },
        meta={},
    )


# ---------------------------------------------------------------------------
# Tool 3: query_swarmia_docs
# ---------------------------------------------------------------------------


@mcp.resource("ui://swarmia/docs-diagnostic.html")
def docs_diagnostic_view() -> str:
    """Interactive documentation diagnostic dashboard."""
    return _load_widget_html("docs-diagnostic")


@mcp.tool(app=AppConfig(resource_uri="ui://swarmia/docs-diagnostic.html"))
def query_swarmia_docs(query: str) -> str:
    """Search the bundled Swarmia documentation for an answer to the user's question.

    Returns the full documentation context prepended with the user's query so
    the LLM can extract the most relevant answer. Keep responses concise —
    max 3 sentences unless the user asks for detail.

    Args:
        query: The user's question about Swarmia.
    """
    logger.info("query_swarmia_docs: %s", query[:80])
    docs_path = Path(__file__).parent / "docs_context.md"

    try:
        docs_content = docs_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "Error: Local documentation corpus (docs_context.md) is missing. "
            "Please reinstall the Swarmia MCP server assets."
        )

    text = (
        f"**User question:** {query}\n\n"
        f"---\n\n"
        f"**Swarmia Documentation Context:**\n\n{docs_content}\n\n"
        f"---\n\n"
        f"Use the documentation above to answer the user's question concisely (max 3 sentences "
        f"unless the user asks for more detail)."
    )

    # Build integration diagnostic signals from the local workspace
    integrations = []

    # GitHub: check if .github/ exists
    has_github = (Path.cwd() / ".github").is_dir()
    integrations.append({
        "name": "GitHub",
        "status": "green" if has_github else "red",
        "detail": "Repository connected" if has_github else "No .github/ directory found",
    })

    # Linear: check if API key is configured
    has_linear = bool(os.getenv("LINEAR_API_KEY"))
    integrations.append({
        "name": "Linear",
        "status": "green" if has_linear else "yellow",
        "detail": "API key configured" if has_linear else "LINEAR_API_KEY not set — regex-only mode",
    })

    # Slack: informational (cannot check locally)
    integrations.append({
        "name": "Slack",
        "status": "yellow",
        "detail": "Configured in Swarmia dashboard (cannot verify locally)",
    })

    # Deployment tracking: check for webhook config
    has_deploy = any(
        "hook.swarmia.com" in (f.read_text(encoding="utf-8", errors="ignore"))
        for f in Path.cwd().rglob("*.yml")
        if f.stat().st_size < 50_000
    )
    integrations.append({
        "name": "Deployment Tracking",
        "status": "green" if has_deploy else "red",
        "detail": "Swarmia webhook found in CI config" if has_deploy else "No deployment webhook configured",
    })

    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content={
            "query": query,
            "answer": "(LLM will summarize from documentation context)",
            "integrations": integrations,
        },
        meta={},
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
