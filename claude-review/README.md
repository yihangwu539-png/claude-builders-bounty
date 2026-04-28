# Claude PR Review Agent

A CLI tool that reviews GitHub pull requests using Claude API and posts structured Markdown comments.

**Bounty:** $150 — powered by [Opire](https://opire.dev)

## Quick Start

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Review a PR
python3 claude-review/pr-review.py --pr https://github.com/owner/repo/pull/123
```

## Features

- **Structured output** — Summary, risks, suggestions, confidence score
- **Zero dependencies** — Uses Python stdlib only (urllib for all API calls)
- **GitHub Action** — Auto-review every PR with the included workflow
- **Configurable** — Custom instructions via `--custom-instructions`

## CLI Usage

```
python3 claude-review/pr-review.py --pr <PR_URL> [options]

Options:
  --pr URL           Full GitHub PR URL (required)
  -o, --output FILE  Save output to file instead of stdout
  --custom-instructions TEXT  Additional context for the review
  --github-token     GITHUB_TOKEN (defaults to GITHUB_TOKEN env var)
```

## Output Format

```markdown
## Summary
(2-3 sentence summary of changes)

### Identified Risks
- Risk 1
- Risk 2

### Improvement Suggestions
1. Suggestion 1
2. Suggestion 2

### Confidence Score
**High** / Medium / Low
```

## GitHub Action

To auto-review every PR, copy `.github/workflows/pr-review.yml` to your repo.
The action runs on every PR and posts a review comment.

## Sample Outputs

### PR: claude-builders-bounty/claude-builders-bounty#5 (n8n workflow, +6,350/-14 lines)

## Summary
Adds a complete n8n weekly dev summary workflow that fetches GitHub activity and generates a narrative report via Claude API. The workflow includes cron scheduling, GitHub API pagination, multi-language support, and Slack delivery.

### Identified Risks
- **Missing screenshot** — No execution screenshot is included; maintainer will need to deploy and verify manually
- **Claude API key exposure** — The workflow reads ANTHROPIC_API_KEY from env, but if n8n credentials are shared, the key could leak
- **No error handling for API failures** — If Claude API is down, the workflow fails silently; no retry or fallback message

### Improvement Suggestions
1. Add a retry node for Claude API calls (n8n supports Error Trigger)
2. Add an optional email fallback if Slack webhook fails
3. Include a .env.example for the config variables

### Confidence Score
**Medium** — Well-structured workflow but lacks error handling and verification screenshot

### PR: claude-builders-bounty/claude-builders-bounty#1 (CHANGELOG skill, +183/-1 lines)

## Summary
Adds a comprehensive CHANGELOG generator as a bash script. It fetches commits since the last git tag, categorizes them into Added/Fixed/Changed/Removed sections, and outputs a formatted CHANGELOG.md file.

### Identified Risks
- **No test suite** — The generated CHANGELOG output is not validated; malformed git history could produce broken output
- **Tag assumption** — If there are no git tags in the repo, the script will error out with `fatal: No names found` with no helpful error message
- **Commit convention dependency** — Relies on conventional commit format; repos without structured commit messages will get "Other" categories for all entries

### Improvement Suggestions
1. Add a fallback when no git tags exist (use `--since` with a date range instead)
2. Add `--dry-run` flag to preview output without writing to file
3. Add support for custom commit category mappings via config file

### Confidence Score
**High** — Clean implementation with good output formatting, tested against real PRs

## Requirements

- Python 3.8+
- ANTHROPIC_API_KEY environment variable
- GITHUB_TOKEN (optional, for private repos — uses GITHUB_TOKEN env var or unauthenticated access)

## Testing

```bash
# Test with real PRs
python3 pr-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/703
python3 pr-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/637
```
