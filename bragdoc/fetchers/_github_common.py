from __future__ import annotations

import os
from datetime import datetime

import requests

API = "https://api.github.com"


def github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN")


def _headers(token: str | None) -> dict:
    token = token or github_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def org_qualifier(orgs: list[str]) -> str:
    return " ".join(f"org:{o}" for o in orgs)


def parse_repo(repository_url: str) -> tuple[str, str]:
    parts = repository_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def pick_issue_date(item: dict) -> datetime:
    pr = item.get("pull_request") or {}
    if pr.get("merged_at"):
        return parse_ts(pr["merged_at"])
    if item.get("closed_at"):
        return parse_ts(item["closed_at"])
    return parse_ts(item["created_at"])


def issue_state(item: dict) -> str:
    pr = item.get("pull_request")
    if pr is not None:
        return "merged" if pr.get("merged_at") else item.get("state", "open")
    return item.get("state", "open")


def search_issues(query: str, token: str | None = None) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        resp = requests.get(
            f"{API}/search/issues",
            headers=_headers(token),
            params={"q": query, "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json().get("items", [])
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items
