from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_reviews import GithubReviewsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_reviews": True},
    )


@responses.activate
def test_fetch_excludes_self_authored(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": [
            {
                "title": "fix ingress bug",
                "html_url": "https://github.com/canonical/nginx/pull/248",
                "number": 248,
                "state": "closed",
                "created_at": "2026-06-01T00:00:00Z",
                "closed_at": "2026-07-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/canonical/nginx",
                "pull_request": {"merged_at": "2026-07-01T00:00:00Z"},
                "user": {"login": "someoneelse"},
            },
            {
                "title": "my own pr",
                "html_url": "https://github.com/canonical/nginx/pull/250",
                "number": 250,
                "state": "open",
                "created_at": "2026-06-05T00:00:00Z",
                "closed_at": None,
                "repository_url": "https://api.github.com/repos/canonical/nginx",
                "pull_request": {"merged_at": None},
                "user": {"login": "octocat"},
            },
        ]},
        status=200,
    )
    items = GithubReviewsFetcher().fetch(_config())
    assert len(items) == 1
    assert items[0].role == "reviewer"
    assert items[0].identifier == "#248"
    assert items[0].source == "github_review"
