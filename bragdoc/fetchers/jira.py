from __future__ import annotations

import os
from datetime import datetime

import requests

from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _parse_jira_ts(value: str) -> datetime:
    # Jira format: 2026-04-10T12:00:00.000+0000 -> add colon in tz offset
    if value[-5] in "+-" and value[-3] != ":":
        value = value[:-2] + ":" + value[-2:]
    return datetime.fromisoformat(value)


class JiraFetcher(Fetcher):
    name = "jira"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and os.environ.get("JIRA_API_TOKEN") is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        server = config.identity["jira_server"].rstrip("/")
        email = config.identity["jira_email"]
        token = os.environ["JIRA_API_TOKEN"]
        start = config.window_start.date().isoformat()
        jql = f'assignee = currentUser() AND updated >= "{start}" ORDER BY updated DESC'
        out: list[WorkItem] = []
        start_at = 0
        while True:
            resp = requests.get(
                f"{server}/rest/api/3/search",
                params={"jql": jql, "startAt": start_at, "maxResults": 50,
                        "fields": "summary,status,updated,project"},
                auth=(email, token),
                headers={"Accept": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for issue in data.get("issues", []):
                fields = issue["fields"]
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
                    extra={},
                ))
            start_at += len(data.get("issues", []))
            if start_at >= data.get("total", 0) or not data.get("issues"):
                break
        return out
