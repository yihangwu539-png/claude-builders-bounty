#!/usr/bin/env python3
"""claude-review.py — Zero-dependency PR review agent using Claude API.

Fetches a PR diff from GitHub and generates a structured Markdown review
via the Claude API. No pip install required — uses only urllib from stdlib.

Usage:
  python claude-review.py --pr https://github.com/owner/repo/pull/123
  python claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
  python claude-review.py --diff-url https://github.com/owner/repo/pull/123.diff

Environment variables:
  ANTHROPIC_API_KEY  — Your Claude API key (required)
  GITHUB_TOKEN       — GitHub token for higher API rate limits (optional)
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error


# ── Helpers ────────────────────────────────────────────────────────────────

def fatal(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def api_request(url, headers=None, data=None, method="GET"):
    """Make an HTTP request using only urllib. Returns (status, body)."""
    req = urllib.request.Request(url, method=method, data=data)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body
    except urllib.error.URLError as exc:
        fatal(f"Network error: {exc.reason}")


def parse_pr_url(url):
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        fatal(f"Invalid GitHub PR URL: {url}\nExpected: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))


# ── GitHub API ─────────────────────────────────────────────────────────────

def fetch_pr_diff(owner, repo, pr_number, github_token=None):
    """Fetch the diff for a pull request via GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    status, body = api_request(url, headers=headers)
    if status != 200:
        fatal(f"GitHub API error (HTTP {status}): {body[:500]}")
    if not body.strip():
        fatal("Empty diff received from GitHub API")
    return body


def fetch_pr_metadata(owner, repo, pr_number, github_token=None):
    """Fetch PR title and description for context."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    status, body = api_request(url, headers=headers)
    if status != 200:
        return {"title": "Unknown", "body": ""}
    data = json.loads(body)
    return {
        "title": data.get("title", "Unknown"),
        "body": data.get("body", "") or "",
    }


# ── Claude API ─────────────────────────────────────────────────────────────

def build_prompt(pr_title, pr_body, diff_text):
    """Build the system and user prompt for Claude."""
    system_prompt = """You are an expert code reviewer. Analyze the provided pull request diff and produce a structured Markdown review. Be thorough, specific, and constructive.

Your review MUST follow this exact format:

## Summary
2-3 sentences summarizing what this PR does and its overall quality.

## Identified Risks
- Risk 1: ...
- Risk 2: ...

## Improvement Suggestions
- Suggestion 1: ...
- Suggestion 2: ...

## Confidence Score
**High** / **Medium** / **Low**

Rate your confidence as:
- **High** — You are very confident in your assessment. The changes are clear, well-scoped, and you can identify specific issues or confirm good practices.
- **Medium** — The changes are moderate in scope, and while you can identify areas of concern or praise, some context may be missing.
- **Low** — The diff is large, complex, or lacks sufficient context for a confident review.

Be specific — reference line numbers, function names, and code patterns where possible."""

    user_prompt = f"""## Pull Request

**Title:** {pr_title}

**Description:**
{pr_body or "(No description provided)"}

## Diff

```diff
{diff_text}
```

Please provide a structured code review following the format specified."""

    return system_prompt, user_prompt


def call_claude_api(system_prompt, user_prompt, api_key):
    """Call the Claude API with the prompts and return the response text."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "User-Agent": "claude-review/1.0",
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    status, body = api_request(url, headers=headers, data=data, method="POST")

    if status != 200:
        fatal(f"Claude API error (HTTP {status}): {body[:500]}")

    result = json.loads(body)
    try:
        text = result["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        fatal(f"Unexpected Claude API response structure: {exc}\nResponse: {body[:500]}")

    return text


# ── CLI ────────────────────────────────────────────────────────────────────

def parse_args():
    """Parse command-line arguments manually (no argparse dependency)."""
    args = {
        "pr_url": None,
        "diff_url": None,
        "diff_text": None,
        "output": None,
    }
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--pr" and i + 1 < len(sys.argv):
            args["pr_url"] = sys.argv[i + 1]
            i += 2
        elif arg == "--diff-url" and i + 1 < len(sys.argv):
            args["diff_url"] = sys.argv[i + 1]
            i += 2
        elif arg == "--diff" and i + 1 < len(sys.argv):
            args["diff_text"] = sys.argv[i + 1]
            i += 2
        elif arg == "--output" and i + 1 < len(sys.argv):
            args["output"] = sys.argv[i + 1]
            i += 2
        elif arg == "--help" or arg == "-h":
            print(__doc__)
            sys.exit(0)
        else:
            fatal(f"Unknown argument: {arg}\n\nUsage:\n  python claude-review.py --pr URL [--output FILE]")
    return args


def main():
    args = parse_args()

    # Get the diff
    if args["pr_url"]:
        owner, repo, pr_number = parse_pr_url(args["pr_url"])
        github_token = os.environ.get("GITHUB_TOKEN") or None
        print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
        diff_text = fetch_pr_diff(owner, repo, pr_number, github_token)
        meta = fetch_pr_metadata(owner, repo, pr_number, github_token)
        pr_title = meta["title"]
        pr_body = meta["body"]
    elif args["diff_url"]:
        # Direct .diff URL — no metadata fetch
        diff_text = api_request(args["diff_url"])[1]
        pr_title = f"PR from {args['diff_url']}"
        pr_body = ""
    elif args["diff_text"]:
        diff_text = args["diff_text"]
        pr_title = "PR (raw diff provided)"
        pr_body = ""
    else:
        fatal("No input specified. Use --pr or --diff-url.\n\nUsage:\n  python claude-review.py --pr https://github.com/owner/repo/pull/123")

    # Get Claude API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        fatal("ANTHROPIC_API_KEY environment variable is not set")

    # Build prompts and call Claude
    print("Analyzing diff with Claude...", file=sys.stderr)
    system_prompt, user_prompt = build_prompt(pr_title, pr_body, diff_text)
    review = call_claude_api(system_prompt, user_prompt, api_key)

    # Add header
    repo_full = f"{owner}/{repo}" if args.get("pr_url") else "external"
    header = f"# PR Review: {repo_full}#{pr_number if args.get('pr_url') else ''}\n\n"
    output = header + review

    # Output
    if args["output"]:
        with open(args["output"], "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Review written to {args['output']}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
