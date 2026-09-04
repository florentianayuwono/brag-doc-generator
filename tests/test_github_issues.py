from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_issues import GithubIssuesFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_issues": True},
    )


@responses.activate
def test_fetch_normalizes_issue(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": [{
            "title": "redirect loop bug",
            "html_url": "https://github.com/canonical/nginx/issues/210",
            "number": 210,
            "state": "closed",
            "created_at": "2026-04-01T00:00:00Z",
            "closed_at": "2026-04-20T00:00:00Z",
            "repository_url": "https://api.github.com/repos/canonical/nginx",
        }]},
        status=200,
    )
    items = GithubIssuesFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_issue"
    assert it.role == "author"
    assert it.state == "closed"
    assert it.identifier == "#210"
    assert it.date == datetime(2026, 4, 20, tzinfo=timezone.utc)
