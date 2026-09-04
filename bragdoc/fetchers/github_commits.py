from __future__ import annotations

import requests

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _search_commits(query: str, token: str | None = None) -> list[dict]:
    items: list[dict] = []
    page = 1
    headers = {
        "Authorization": f"Bearer {token or gh.github_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    while True:
        resp = requests.get(
            f"{gh.API}/search/commits",
            headers=headers,
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


class GithubCommitsFetcher(Fetcher):
    name = "github_commits"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        query = f"author:{user} author-date:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            query += f" {orgs}"
        out: list[WorkItem] = []
        for item in _search_commits(query):
            repo_info = item.get("repository", {})
            repo = repo_info.get("name", "")
            org = (repo_info.get("owner") or {}).get("login")
            message = item["commit"]["message"].splitlines()[0]
            out.append(WorkItem(
                source="github_commit",
                project=repo,
                org=org,
                title=message,
                url=item["html_url"],
                date=gh.parse_ts(item["commit"]["author"]["date"]),
                role="author",
                state=None,
                identifier=item["sha"][:7],
                extra={},
            ))
        return out
