#!/usr/bin/env python3
"""Generate custom GitHub profile SVGs for the profile README.

Requires GITHUB_TOKEN (or GH_TOKEN) for the GitHub GraphQL API.
The script uses only Python's standard library.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = os.getenv("GITHUB_USERNAME", "ahmedkamalrezk")
TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
OUT = Path(__file__).resolve().parents[1] / "assets"
OUT.mkdir(parents=True, exist_ok=True)


def request_json(url: str, payload: dict | None = None, headers: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def graphql(query: str):
    if not TOKEN:
        raise RuntimeError("Set GITHUB_TOKEN or GH_TOKEN to generate live profile statistics.")
    return request_json(
        "https://api.github.com/graphql",
        {"query": query},
        {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-generator",
        },
    )


def svg_header(width: int, height: int, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
    )


def generate_contributions():
    today = date.today()
    start = today - timedelta(days=363)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount color }
            }
          }
        }
      }
    }
    """
    result = graphql(query % {}) if False else graphql_with_variables(
        query,
        {
            "login": USERNAME,
            "from": f"{start.isoformat()}T00:00:00Z",
            "to": f"{today.isoformat()}T23:59:59Z",
        },
    )
    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    width, height = 1000, 160
    cell, gap, left, top = 11, 4, 18, 42
    parts = [
        svg_header(width, height, f'{calendar["totalContributions"]} GitHub contributions in the last year'),
        '<rect width="100%" height="100%" rx="12" fill="#0d1117" stroke="#30363d"/>',
        '<text x="18" y="25" fill="#e6edf3" font-family="Arial,sans-serif" font-size="14" font-weight="600">Contribution activity</text>',
        f'<text x="{width-18}" y="25" text-anchor="end" fill="#8b949e" font-family="Arial,sans-serif" font-size="11">{calendar["totalContributions"]} contributions in the last year</text>',
    ]
    month_labels = {}
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            d = date.fromisoformat(day["date"])
            if d.day <= 7:
                month_labels[(wi, d.strftime("%b"))] = True
            weekday = d.weekday()
            # GitHub calendar starts Sunday; convert Monday-based weekday.
            row = (weekday + 1) % 7
            x, y = left + wi * (cell + gap), top + row * (cell + gap)
            color = day.get("color") or "#161b22"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{escape(color)}"><title>{escape(day["date"])}: {day["contributionCount"]} contributions</title></rect>'
            )
    for wi, month in month_labels:
        x = left + wi * (cell + gap)
        parts.append(f'<text x="{x}" y="145" fill="#8b949e" font-family="Arial,sans-serif" font-size="10">{escape(month)}</text>')
    parts.append("</svg>")
    (OUT / "contributions.svg").write_text("".join(parts), encoding="utf-8")


def graphql_with_variables(query: str, variables: dict):
    if not TOKEN:
        raise RuntimeError("Set GITHUB_TOKEN or GH_TOKEN to generate live profile statistics.")
    return request_json(
        "https://api.github.com/graphql",
        {"query": query, "variables": variables},
        {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-generator",
        },
    )


def generate_stats():
    query = """
    query($login: String!) {
      user(login: $login) {
        name
        followers { totalCount }
        repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
        starredRepositories { totalCount }
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalRepositoryContributions
        }
      }
    }
    """
    payload = graphql_with_variables(query, {"login": USERNAME})
    user = payload["data"]["user"]
    contributions = user["contributionsCollection"]
    metrics = [
        ("PUBLIC REPOS", user["repositories"]["totalCount"]),
        ("FOLLOWERS", user["followers"]["totalCount"]),
        ("STARS GIVEN", user["starredRepositories"]["totalCount"]),
        ("COMMITS", contributions["totalCommitContributions"]),
        ("PULL REQUESTS", contributions["totalPullRequestContributions"]),
        ("ISSUES", contributions["totalIssueContributions"]),
    ]
    width, height = 760, 190
    parts = [
        svg_header(width, height, f"GitHub statistics for {USERNAME}"),
        '<rect width="100%" height="100%" rx="12" fill="#0d1117" stroke="#30363d"/>',
        '<text x="24" y="30" fill="#e6edf3" font-family="Arial,sans-serif" font-size="15" font-weight="600">GitHub overview</text>',
    ]
    positions = [(24, 58), (274, 58), (524, 58), (24, 122), (274, 122), (524, 122)]
    for (label, value), (x, y) in zip(metrics, positions):
        parts.extend([
            f'<rect x="{x}" y="{y}" width="212" height="48" rx="8" fill="#161b22" stroke="#30363d"/>',
            f'<text x="{x+14}" y="{y+20}" fill="#8b949e" font-family="Arial,sans-serif" font-size="10">{escape(label)}</text>',
            f'<text x="{x+14}" y="{y+39}" fill="#69e0c2" font-family="Arial,sans-serif" font-size="17" font-weight="700">{value:,}</text>',
        ])
    parts.append("</svg>")
    (OUT / "stats.svg").write_text("".join(parts), encoding="utf-8")


def main():
    if not TOKEN:
        raise SystemExit("Missing GITHUB_TOKEN. Add a token to the GitHub Actions secret or environment.")
    payload = graphql_with_variables(
        "query($login: String!) { user(login: $login) { login } }",
        {"login": USERNAME},
    )
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    generate_contributions()
    generate_stats()
    print(f"Updated profile SVGs for @{USERNAME}")


if __name__ == "__main__":
    main()
