## Swarmia Docs MCP
**Documentation DevEx experiment**

2026-02-22

[Static knowledge bases are dead](https://www.reddit.com/r/SaaS/comments/1q86tzp/the_concept_of_static_knowledge_bases_is_dying/). Developer tooling grows increasingly complex &ndash; and traditional KBs are not cutting it. **Today,** when developers face integration or troubleshooting issues with platforms like Swarmia, they are forced to break their workflow, context-switch to a web browser, click through documentation. This traditional "pull" model of support relies entirely on the developer to find generic instructions and translate them into their specific local environment. This process is **slow, inefficient, and highlights the need for documentation that converges with tooling.**

This project introduces a set of context-aware IDE Skills backed by a custom MCP Server. By shifting from static documentation to interactive, agentic workflows, developers can **simply invoke commands** like ``/swarmia-troubleshooting`` or ``/swarmia-integrate`` directly within the IDE. Instead of providing links to documentation, the MCP server actively assesses the developer's local environment &ndash; such as git configurations and repository state &ndash; to provide dynamic, interactive solutions, without requiring the developer to leave their IDE: 

* Automatically scaffold integrations
* Fix commit hygiene issues
* ...

---

# Usage

Very clear, very concise usage instructions, with examples. Details latger

```bash
# Use case: Your Swarmia is up and running
# Invoke troubleshoot Skill, it will use MCP to respond with facts inside a UI
/swarmia-troubleshoot
```

```bash
# Use case: Your Swarmia needs configuration or initial setup
# Invoke troubleshoot Skill, it will use MCP to respond with facts inside a UI
/swarmia-integrate
```

# Video

include screencast

# Details

all details here