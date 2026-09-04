from __future__ import annotations

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


class GithubReviewsFetcher(Fetcher):
    name = "github_reviews"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        query = f"reviewed-by:{user} type:pr updated:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            query += f" {orgs}"
        out: list[WorkItem] = []
        for item in gh.search_issues(query):
            author = (item.get("user") or {}).get("login")
            if author == user:
                continue
            org, repo = gh.parse_repo(item["repository_url"])
            out.append(WorkItem(
                source="github_review",
                project=repo,
                org=org,
                title=item["title"],
                url=item["html_url"],
                date=gh.pick_issue_date(item),
                role="reviewer",
                state=gh.issue_state(item),
                identifier=f"#{item['number']}",
                extra={"author": author},
            ))
        return out
