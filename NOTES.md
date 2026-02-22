# STDIO vs HTTP

**Choice:** stdio transport over Streamable HTTP. While HTTP is great for centralized, remote context, the core value of this Swarmia agent is assessing the developer's local, unpushed workspace—like checking if their local branch name follows the Jira naming convention. By deploying it as a stdio child process managed by the IDE, we get zero-latency access to the local file system without opening local network ports, avoiding firewall issues, or dealing with localhost port conflicts. It’s a secure, production-ready way to deliver local developer experience. Downsides are billing, access control, usage metrics.

**Note 2:**