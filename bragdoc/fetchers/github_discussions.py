from __future__ import annotations

import requests

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem

_QUERY = """
query($q: String!) {
  search(query: $q, type: DISCUSSION, first: 100) {
    nodes {
      ... on Discussion {
        title
        url
        number
        createdAt
        repository { name owner { login } }
      }
    }
  }
}
"""


class GithubDiscussionsFetcher(Fetcher):
    name = "github_discussions"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        q = f"author:{user} created:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            q += f" {orgs}"
        headers = {
            "Authorization": f"Bearer {gh.github_token()}",
            "Accept": "application/vnd.github+json",
        }
        resp = requests.post(
            f"{gh.API}/graphql",
            headers=headers,
            json={"query": _QUERY, "variables": {"q": q}},
            timeout=30,
        )
        resp.raise_for_status()
        nodes = resp.json()["data"]["search"]["nodes"]
        out: list[WorkItem] = []
        for node in nodes:
            if not node:
                continue
            repo_info = node.get("repository", {})
            out.append(WorkItem(
                source="github_discussion",
                project=repo_info.get("name", ""),
                org=(repo_info.get("owner") or {}).get("login"),
                title=node["title"],
                url=node["url"],
                date=gh.parse_ts(node["createdAt"]),
                role="author",
                state=None,
                identifier=f"#{node['number']}",
                extra={},
            ))
        return out
