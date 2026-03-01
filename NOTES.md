# Roadmap notes

- Add Cloudflare Code Mode, see ``md/code-mode _scoping.md`` - huge quality jump for complex questions (something something docs and what does this mean for my repo's PR merge time), plus out of the box zero-leak security for API keys (sec scanner hinted at this, CM would add "Supervisor"), plus perfect oberservability (identify pain points). Requires substantial refactoring - changes to all tools, adding a remote server (features split into local and remote MCP). Role of MCP Apps unclear.
- ...

# Random notes

## STDIO vs HTTP

**Stdio transport over Streamable HTTP.** While HTTP is great for centralized, remote context, the core value of this Swarmia agent is assessing the developer's local, unpushed workspace &ndash; like checking if their local branch name follows the Jira naming convention. By deploying it as a stdio child process managed by the IDE, we get zero-latency access to the local file system without opening local network ports, avoiding firewall issues, or dealing with localhost port conflicts. It’s a secure, production-ready way to deliver local developer experience. Downsides are billing, access control, usage metrics. **Control plane VS Asset plane:** JSN-RPC transport via stdio (control), even though "mcp-app-template" uses HTTP for asset transport (widgets/iframes). Not a contradiction, regular use case.

### MCP server Type 1: The "Infrastructure & Data" Agent (Docker wins)

Example: Web API MCP Server. "Data lake" project = Type 1.

* **Goal:** Connect the LLM to a specific database, third-party API, or isolated data processing pipeline.
* **Docker wins:** LLM is executing SQL queries or writing parquet files to a data lake. Isolation and strict boundary needed (a volume mount), defining exactly where it is allowed to read and write. Don't want a hallucinating agent accidentally writing a 5GB data dump into ``home``.
* *Examples:* Postgres MCP servers, GitHub Cloud API wrappers, Data Lake ETL agents.

### MCP Server Type 2: The "Workspace Context" Agent (`uv` wins)

* **Goal:** Act as a pair programmer that looks over the developer's shoulder at whatever code they are currently writing.
* **`uv` wins:** The target is dynamic. Dev opens `repo-A` in VS Code at 9 AM, and `repo-B` at 10 AM. Agent needs to instantly read the `.git` folder of whichever one is active. If this was in Docker, container with new volume mounts might have to be destroyed/rebuilt every time a new folder is opened in the IDE.
* *Examples:* Git hygiene checkers, code linters, local file scaffolders.

## Testing

**MCP Inspector:** Constantly reloading the IDE chat window is slow. The official MCP Inspector allows testing Python tools in a browser sandbox before connecting them to VS Code. In a separate terminal:

`npx @modelcontextprotocol/inspector uv run server.py`

Opens a local web page. Manually click "Call Tool" on ``check_swarmia_commit_hygiene`` -- result is the generated JSON schema FastMCP and what stdout Python script returned. 

## Distribution

**Portability:** Creating a Dockerfile would be a trap because of **file system isolation**. Swarmia Skills derive value from reading the local, unpushed workspace. They need to run `git log` on  current projects and read local `CODEOWNERS` file. Correct way to build MCP portability: **containerize only the Python environment**, using **`uv`** (Zero-install execution). *Install:* `uvx` or `uv run` (Python version and dependencies downloaded on the fly). Prerequisit: uv. VS Code / Claude Desktop config: -- see README

---

## Talking points

### Talking Point - Architectural tradeoff: Docker vs uv

*"First instinct is containerizing with Docker. Previous MCP server (with local data lake), was using Docker with explicit volume mounts = huge advantage for access control and isolating the data footprint. Swarmia IDE agent is different. It’s a 'Workspace Context' agent, not an 'Infrastructure' agent. It needs frictionless, dynamic access to the currently opened repo. Forcing that through dynamic Docker volume mounts creates a brittle user experience. Versus: Packaging it with **`uv`= zero-config portability of a container, with the native file-system access required to check local git.***

### Talking Point - Architectural tradeoff: Number of Skills

*UX for the IDE deliberately avoids creating a separate slash command for every tool. 1-to-1 mapping is a legacy CLI mindset. It forces the dev to memorize commands and self-diagnose. Instead, one single /swarmia Skill acts as an intelligent router. From highly descriptive docstrings (MCP Tools), the LLM dynamically decides whether to query the docs, check local git hygiene, or scaffold YAML. The LLM can even chain them together to solve a problem in a single prompt. It **shifts the cognitive load from the developer to the Agent.***

### Talking Point - Dependencies in server.py for portability

*Server.py being a local workspace tool, file-system isolation issues of Docker should be worked around. Instead, ``uv`` handles the environment. For a production release, standard ``pyproject.toml`` would be used. For this prototype, ``PEP 723`` (inline script metadata) is used. All dependencies are defined in server.py. A dev pulls this single file and executes ``uv run server.py`` - uv dynamically provisions the exact Python version and dependencies on the fly, with zero setup or virtual environment management required by the user. Fastest possible Time-to-Value for a local CLI tool.*

### Talking Point - "Stateless design"

*Absence of Swarmia PAT **reduces developer friction**. Core features to require **zero Swarmia authentication**. A big hurdle to developer tooling adoption is the 'Token Dance' - making a dev stop what they are doing, log into a web portal, generate a PAT, paste it into their IDE. This agent focuses on local git hygiene and generating deployment scaffolding, it can provide immediate 'Time to Value' on Day 1 without ever requiring the developer to generate a Swarmia API key. It just enforces the rules locally and uses the developer's existing Linear access."*

We architected a "bottom-up" local workspace agent, as opposed to a "top-down" data scraper. The MCP server is stateless (almost). Advantage of this "Zero Swarmia Auth" angle -- ***check README for up-to-date:***

> **Git hygiene tool** - `check_swarmia_commit_hygiene` runs locally. It reads the local file system using `git log`. Live issue verification talks to the **Linear API** (using my Linear PAT). The tool never needs to talk to Swarmia's backend because it is simply enforcing Swarmia's *formatting rules* before the code is pushed to GitHub.

> **Deployment scaffolding tool** - `scaffold_swarmia_deployment` tool is just a highly intelligent text generator. It inspects the local `.github/workflows` folder and generates the YAML snippet. 

> **The Documentation tool** - `query_swarmia_docs` is just scraping or using RAG of a public help center (`help.swarmia.com`). No authentication required. **But also:** 

- *Deployment token:* Swarmia *does* require a token to accept the webhook. But the MCP server does not need to hold it. The MCP agent simply generates the YAML that says: `Authorization: Bearer ${{ secrets.SWARMIA_DEPLOYMENT_TOKEN }}` and instructs the user: *"I've generated the pipeline code. Please grab your deployment token from your Swarmia settings and drop it into your GitHub Secrets."*
- ``/swarmia-admin``, if implemented, would generate and use an API token, for **Context/Team Mapping type tools**.Example: Agent reads the local `.github/CODEOWNERS` file and wants to ping Swarmia's backend to say, *"Does the `@my-org/frontend` team actually exist in Swarmia yet?"*. Requires a Swarmia API key to hit the `GET /api/v0/teams` endpoint.


### Talking point: ``scaffold_swarmia_deployment`` tool's inject behavior

The server should not directly modify the YAML files. Nightmare of edge cases around the corner. The custom tools only handle their domain logic, the IDE handles file editing. 

*The ``scaffold_swarmia_deployment`` tool is a pure generator with zero filesystem write permissions. As a developer, I don't want a background Python script silently mutating my CI/CD pipelines. Especially since programmatic YAML parsers often strip out comments and ruin formatting. Instead, the MCP tool returns the perfect snippet to the LLM. Because we are operating inside an IDE like VS Code, the LLM then uses the IDE's native file-editing tools to present a beautiful, reversible inline diff to the user. It separates the intelligence domain (knowing the Swarmia webhook format) from the execution domain (safely editing files)."*

### Talking point: Regex vs LIN issue detection

There are 2 methods to detect an issue, the real way if connection to Linear exists, and a smoke and mirror way using regex, for presentation purposes. 

### Talking point: Phase 1, Phase 2 during development will leave behind some fragments

*In Phase 1, FastMCP's standard inline decorators was used. This got the project off the ground immediately. During Phase 2, there is a paradigm clash: the UI template relies on dynamic file discovery, while FastMCP expects static decorators. A dynamic adapter layer is required. The main server loop iterates over the widget directory, extracts the UI metadata, and programmatically binds the handle() functions to the FastMCP registry. Advantages: Architectural scalability of the UI template, without losing the rock-solid protocol handling of FastMCP.*


---

# The 2nd Skill (``/swarmia-admin`` with DevOps persona)

My pitch is about the death of static knowledge bases and the rise of **executable documentation**. If `/swarmia-admin` ends up looking like a CLI automation tool, it distracts from the "docs+tool" philosophy. However, from a Post-Sales/TSE angle, there is a cluster of advantages to having that 2nd Skill:

1. **A "Setup Guide" is the Ultimate Dead Document:** It's the type of documentation that causes the most friction, confusion, and support tickets. Not the end-user feature docs do that, but the **Admin onboarding & setup guides**. Static admin docs are notoriously awful: *"Go to Settings > Click X > Copy Y > Paste into Z > Ensure checkbox A is checked."* ... **The pitch:** *`/swarmia-admin` proves that complex, multi-step onboarding documentation can be transformed into an executable agent. Instead of reading a doc on how to map a Linear team to a Swarmia team, the admin just types '/swarmia-admin I connected Linear, are my teams mapped?' -- the agent reads the documentation's rules, checks the API, and does it for them."* ... **Procedural knowledge** is hard do document and better served as an interactive wizard than a static page.

2. **Knowledge is Persona-dependent:** A core problem with static Help Centers is that they force the user to self-select their persona. A developer searching "Linear integration" gets the exact same article as the Engineering Director, even though they need entirely different information. ... **The pitch:** *"Documentation is about the context of the person asking. Next-generation documentation must be role-aware. When a dev uses `/swarmia`, the knowledge is projected locally. This is about fixing a git commit. When a manager uses `/swarmia-admin`, the knowledge is projected globally. This is about checking DORA webhook configurations. The doc+tool 'document' morphs to fit the user's blast radius."* ... **Docs+tool** is fundamentally rethinking how technical knowledge is categorized and delivered.

3. **Empathy for the "champion" (the TSE perspective):** In Post-Sales, the person who actually bought Swarmia (the Staff Engineer or Engineering Manager) is the champion. The individual contributors (the devs) are just the end-users.

* Developer-focused tooling is only solving a localized workflow problem.
* Admin-focused tooling is only solving the *Champion's* problem.
* Docs+tool: *"Admin skill was added, because from a support perspective, the person deploying Swarmia is the one bearing the cognitive load of reading the documentation and enforcing it across 50 developers. The `/swarmia-admin` skill takes the burden of 'enforcing the docs' off the manager's plate and builds it directly into the deployment workflow."*

That said, this 2nd Skill might not be finished in time. Priority is on single Skill mode. Or just show the SKILL.md verbatim.

*"The `/swarmia` Skill shows that local documentation should be executable. But because I come from a TSE background, I know the real support burden is on the onboarding admins. The `/swarmia-admin` SKill replaces the 'Getting Started' guides by turning API config into an interactive chat."*

- Grand vision of a Product Manager
- Empathy of a Support Engineer
- Chops of a Developer

---

# Use cases

Check README, might have done some already and forgot

## Realistic use case 1:

Dev:

```bash
``/swarmia`` I just joined the team. How do I make sure my code gets tracked, and is my current branch okay?
```

With a single Skill, the Agent will do this autonomously in one thought process:

- Call ``query_swarmia_docs`` (Search: "How to track code") -> Learns that Swarmia needs Jira tickets in branch names and .github/workflows configured.
- Call ``check_swarmia_commit_hygiene`` -> Checks the local git branch and sees it's named fix-auth-bug (missing a ticket).
- Call ``scaffold_swarmia_deployment`` -> Checks for the YAML file and sees it's missing.

Response to Dev: 

*"Welcome to the team! According to Swarmia docs, we track work using Jira tickets in branch names. I checked your current branch, and it's missing a Jira ID. Want me to rename it? Also, I noticed you don't have the Swarmia deployment webhook in your GitHub Actions yet—should I scaffold that for you?"*



## Realistic use case 2

Screen share with VS Code open:

1. Create dummy branch: `git checkout -b fix-bug`
2. Run MCP Skill: `/swarmia Is my current branch going to be tracked properly?`
3. LLM should 
  - autonomously `check_swarmia_commit_hygiene`
  - notice the branch name lacks the `ENG-` prefix
  - reply: *"Your branch is missing a Linear ID. Shall I rename it for you?"*

This shows: 

- Swarmia's data model
- how issue trackers feed into it
- and local AI agents enforce that data hygiene in real-time
