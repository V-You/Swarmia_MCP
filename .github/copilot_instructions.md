# Swarmia MCP Server Developer Instructions

You are an expert Python engineer building a local Model Context Protocol (MCP) server for a Swarmia integration.

## Architecture Rules
1. **Framework:** Strictly use the `fastmcp` library (`from fastmcp import FastMCP`). Do NOT use the raw `mcp.server` low-level APIs.
2. **Transport:** The server is intended to be run locally as a child process by an IDE. Always use `stdio` transport. Never configure HTTP/SSE or open network ports.
3. **Typing & Docstrings:** FastMCP relies heavily on Python type hints and docstrings to automatically generate JSON schemas for the LLM. You MUST provide detailed docstrings and strict type hints for every function decorated with `@mcp.tool` or `@mcp.resource`.

## Capabilities to Implement
Whenever I ask you to add a feature, consider if it should be a:
- **Tool (`@mcp.tool`):** For actions with side effects (e.g., executing a local `git` command, making a POST request to the Swarmia API to create a webhook).
- **Resource (`@mcp.resource`):** For read-only data (e.g., reading the local `.github/workflows/deploy.yml` or reading `CODEOWNERS`).

If a command requires reading the local file system or running a `git` command, use standard Python libraries (`subprocess`, `pathlib`). Assume the server is running in the root of the user's workspace.