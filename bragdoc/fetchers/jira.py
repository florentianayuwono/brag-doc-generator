from __future__ import annotations

import os
import re
from datetime import datetime

import requests

from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem

_REPO_URL_RE = re.compile(r"github\.com/[^/]+/([^/]+?)(?:/|$)")


def _parse_jira_ts(value: str) -> datetime:
    # Jira format: 2026-04-10T12:00:00.000+0000 -> add colon in tz offset
    if value[-5] in "+-" and value[-3] != ":":
        value = value[:-2] + ":" + value[-2:]
    return datetime.fromisoformat(value)


def parse_dev_status_repo(data: dict) -> str | None:
    """Extract a GitHub repo name from a Jira dev-status detail response."""
    for detail in data.get("detail", []):
        for pr in detail.get("pullRequests", []):
            url = pr.get("url") or pr.get("repositoryUrl") or ""
            match = _REPO_URL_RE.search(url)
            if match:
                return match.group(1)
    return None


class JiraFetcher(Fetcher):
    name = "jira"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and bool(os.environ.get("JIRA_API_TOKEN"))

    def _linked_repo(self, server: str, auth: tuple[str, str], issue_id: str) -> str | None:
        # Jira's Development panel data (linked branches/PRs) lives behind this
        # undocumented-but-stable endpoint. Best-effort: any failure just means
        # we fall back to other linking heuristics, never breaks the fetch.
        try:
            resp = requests.get(
                f"{server}/rest/dev-status/1.0/issue/detail",
                params={"issueId": issue_id, "applicationType": "GitHub",
                        "dataType": "pullrequest"},
                auth=auth,
                headers={"Accept": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            return parse_dev_status_repo(resp.json())
        except Exception:  # noqa: BLE001 - dev-status linking is best-effort
            return None

    def fetch(self, config: Config) -> list[WorkItem]:
        server = config.identity["jira_server"].rstrip("/")
        email = config.identity["jira_email"]
        token = os.environ["JIRA_API_TOKEN"]
        auth = (email, token)
        start = config.window_start.date().isoformat()
        jql = f'assignee = currentUser() AND updated >= "{start}" ORDER BY updated DESC'
        out: list[WorkItem] = []
        next_page_token: str | None = None
        while True:
            body = {
                "jql": jql,
                "maxResults": 50,
                "fields": ["summary", "status", "updated", "project"],
            }
            if next_page_token:
                body["nextPageToken"] = next_page_token
            resp = requests.post(
                f"{server}/rest/api/3/search/jql",
                json=body,
                auth=auth,
                headers={"Accept": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for issue in data.get("issues", []):
                fields = issue["fields"]
                issue_id = issue.get("id")
                linked_repo = self._linked_repo(server, auth, issue_id) if issue_id else None
                out.append(WorkItem(
                    source="jira",
                    project=fields["project"]["key"],
                    org=None,
                    title=fields["summary"],
                    url=f"{server}/browse/{issue['key']}",
                    date=_parse_jira_ts(fields["updated"]),
                    role="author",
                    state=fields["status"]["name"],
                    identifier=issue["key"],
                    extra={"linked_repo": linked_repo} if linked_repo else {},
                ))
            if data.get("isLast", True) or not data.get("nextPageToken"):
                break
            next_page_token = data["nextPageToken"]
        return out
