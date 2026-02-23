# Swarmia Documentation Context

> Bundled reference for the `query_swarmia_docs` MCP tool.
> Source: https://help.swarmia.com/ (retrieved 2026-02-22)

---

## What is Swarmia?

Swarmia is a software engineering intelligence platform designed to provide actionable insights and visibility to modern engineering organizations. By integrating your development tools, Swarmia helps you collaborate effectively, streamline workflows, and deliver the right features faster.

---

## Getting Started (15 minutes)

### Step 1: Install Swarmia to GitHub

1. Ensure you have admin permissions on GitHub.
2. Find [Swarmia in the GitHub Marketplace](https://github.com/marketplace/swarmia).
3. Click **Install**, review authorizations, and click **Install & Authorize**.

> **Note:** All users in your organization can read metadata (such as Pull Request names) for all integrated repositories. Swarmia collects file names and size of commits but does **not** store your source code.

### Step 2: Connect your issue tracker

**Jira:**
1. Ensure you have Jira admin permissions.
2. Navigate to [Jira settings in Swarmia](https://app.swarmia.com/settings/jira).
3. After sync, assign issue ownership for teams.

**Linear:**
1. Ensure you have Linear admin permissions.
2. Navigate to [Linear settings in Swarmia](https://app.swarmia.com/settings/linear).

### Step 3: Connect your notifications platform

**Slack:**
1. Ensure you have Slack admin permissions.
2. Navigate to [Slack settings in Swarmia](https://app.swarmia.com/settings/slack).
3. Review permissions and click Allow.

**Microsoft Teams:**
1. Ensure you have Entra SSO and Teams Administrator role.
2. Navigate to [Microsoft Teams settings in Swarmia](https://app.swarmia.com/settings/microsoft-teams).

Most engineers interact with Swarmia through Slack or Microsoft Teams — receiving personal notifications, team digests, and feedback on working agreements.

### Step 4: Create teams

Create teams in Swarmia to ensure work gets assigned correctly. Swarmia automatically merges most user identities and removes duplicates. You can create teams by:
- Creating teams manually
- Importing from GitHub
- Using the Swarmia Teams API

---

## Linking Pull Requests to Issues

Linking PRs to issues enables deeper insights. Without it, Swarmia can only show issue tracker data, not actual coding activity.

**Features that require PR–issue linking:**
- Investment balance
- Software capitalization
- Work log by issue
- Initiatives

### Automatic detection methods:
- Mention the issue key in the PR title (e.g., `Foobar [CLOUD-123]`)
- Mention the issue key at the beginning of the PR description
- Add the issue key URL in the PR description
- Start the branch name with the issue key (e.g., `CLOUD-123-foo`) or use it after a slash (e.g., `myname/bug/CLOUD-123-foo`)

### AI suggested issue links:
Swarmia can automatically suggest relevant issues for unlinked PRs via Slack notifications when a developer merges a PR.

---

## Deployment Tracking

Deployments are the data source for DORA metrics: deployment frequency, change failure rate (CFR), and mean time to recovery (MTTR).

### Deployment data sources:
- **Merged pull requests** — use merges into a specific branch as the proxy
- **GitHub Checks** — automatically create deployments from CI/CD pipeline
- **GitHub Deployments** — automatically create deployments from GitHub Deployments
- **Deployments API** — send deployment data directly via HTTP POST, supports multiple environments

### Setting up via the Deployments API:

1. Navigate to [Settings → Deployments](https://app.swarmia.com/settings/deployments)
2. Create a new application and give it a name
3. Select "Send deployment data via the API" as the Deployment source
4. Get the API token and store it securely
5. Save your deployment configuration

**Endpoint:** `POST https://hook.swarmia.com/deployments`

**Authorization:** Send the `Authorization` header with the access token.

**Required fields:**
- `version` (string) — version identifier (semantic version, release tag, or commit hash)
- `appName` (string) — identifier for the app/system
- `repositoryFullName` (string, required if `commitSha` is given) — e.g., `octocat/example`

**Optional fields:**
- `environment` (string) — e.g., `production` or `staging` (defaults to `default`)
- `deployedAt` (string) — ISO 8601 timestamp (defaults to current time)
- `description` (string) — shown in Deployment Insights tooltip (max 2048 chars)
- `commitSha` (string) — full SHA of latest commit in the deployment
- `includedCommitShas` (string[]) — manually specify which commits the deployment contains
- `filePathFilter` (string) — filter PRs by file path (useful for monorepos)

### Example curl request:
```bash
curl -X POST https://hook.swarmia.com/deployments \
  -H "Authorization: $AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v2.0.5",
    "appName": "frontend",
    "environment": "production",
    "commitSha": "3fc4a317364fa427cfa8238369eb8535aa1d1670",
    "repositoryFullName": "octocat/example"
  }'
```

### Fix deployments:
Same as a regular deployment, but with an additional required field:
- `fixesVersion` (string) — version of the previous deployment that introduced the issue

### GitHub Actions example:
```yaml
- name: Send deployment to Swarmia
  if: success()
  run: |
    JSON_STRING=$( jq --null-input --compact-output \
      --arg version "${{ github.sha }}" \
      --arg appName "<YOUR_APP>" \
      --arg environment "production" \
      --arg commitSha "${{ github.sha }}" \
      --arg repositoryFullName "${{ github.repository }}" \
      '{"version": $version, "appName": $appName, "environment": $environment, "commitSha": $commitSha, "repositoryFullName": $repositoryFullName}' )
    curl -H "Authorization: ${{ secrets.SWARMIA_DEPLOYMENTS_AUTHORIZATION }}" \
      -H "Content-Type: application/json" \
      -d "$JSON_STRING" \
      https://hook.swarmia.com/deployments
```

After setup, remember to:
1. Add `SWARMIA_DEPLOYMENTS_AUTHORIZATION` secret to GitHub
2. Change `<YOUR_APP>` to the relevant app name

---

## DORA Metrics

Swarmia's DORA and deployment insights help you analyze deployment trends across your organization.

### Deployment Frequency
How often code is deployed to production. "Elite" teams deploy on-demand or multiple times per day; "high-performing" teams deploy between once per day and once per week. A low deployment frequency can indicate working with large batches or poor deployment infrastructure.

### Change Lead Time
Time from first commit to production deployment. "Elite" teams: less than an hour. "High-performing" teams: one day to one week. High change lead time can indicate large batch sizes, slow code review/QA, or long CI/CD wait times.

### Time to Deploy
Time from PR merge to deployment. Part of change lead time. Useful for understanding how much delay your deployment process causes.

### Change Failure Rate (CFR)
Percentage of deployments that cause defects impacting end-users. Swarmia uses deployments as the basis — deploys that fix other deploys (patch, hotfix, rollback, forward fix) mark the original deploy as a failure.

### Mean Time To Recovery (MTTR)
Average time to address change failures. Time to recovery = time between an original deploy and the fix for the problem.

### Automatic change failure detection:
Swarmia can automatically detect change failures from rollbacks or reverted pull requests.

---

## Pull Request Cycle Time

Cycle time measures how long it takes for a pull request to go from first commit to merge. It is a systemic measure affected by:
- Code review process
- Manual testing process
- Amount of multitasking
- Dependencies
- Domain knowledge

It is **not** an individual productivity metric.

### Prerequisites:
- GitHub connected
- At least one team created

### Tips for improvement:
- Use the pull request inbox view
- Enable Slack/Teams notifications for timely updates
- Use digests (daily/weekly)
- Adopt working agreements (merge PRs in X days, review in X days, limit WIP)
- Keep batch sizes small — smaller changes are easier to review and less risky

---

## Investment Balance

Helps engineering teams understand how they balance efforts across priorities.

### The Balance Framework (recommended starting point):
- **New things:** New products and features
- **Improvements:** Enhancing existing features, tools, or processes
- **Productivity:** Making it easier to get work done in the future
- **Keeping the lights on (KTLO):** Maintaining existing systems and services

**Healthy balance:** 10-15% productivity, KTLO under 30%, remaining 60% for new things and improvements.

### Setup:
1. Create an investment breakdown (or use the Balance framework)
2. Define rules to auto-categorize work
3. Link pull requests to issues for accuracy

Once highest-level work items are categorized (e.g., initiatives or epics), Swarmia processes the issue hierarchy automatically to categorize all remaining child issues.

---

## Working Agreements

Working agreements help teams define and enforce best practices:
- Merge pull requests within X days
- Review pull requests within X days
- Limit pull requests in progress to X
- Link pull requests to issues

Swarmia sends Slack/Teams reminders when agreements are at risk of being broken.

---

## Key URLs

- Swarmia App: https://app.swarmia.com
- GitHub Marketplace: https://github.com/marketplace/swarmia
- Deployment Settings: https://app.swarmia.com/settings/deployments
- DORA Metrics: https://app.swarmia.com/metrics/dora
- Deployments: https://app.swarmia.com/infrastructure/deployments
- Investment Balance: https://app.swarmia.com/investment
- Working Agreements: https://app.swarmia.com/working-agreements
- Support: hello@swarmia.com
