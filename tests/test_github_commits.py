from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_commits import GithubCommitsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_commits": True},
    )


@responses.activate
def test_fetch_normalizes_commit(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/commits",
        json={"items": [{
            "sha": "abcdef1234567890",
            "html_url": "https://github.com/canonical/aproxy-operator/commit/abcdef1234567890",
            "commit": {
                "message": "Fix proxy bug\n\nlong body",
                "author": {"date": "2026-05-14T09:00:00Z"},
            },
            "repository": {"name": "aproxy-operator", "owner": {"login": "canonical"}},
        }]},
        status=200,
    )
    items = GithubCommitsFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_commit"
    assert it.title == "Fix proxy bug"
    assert it.identifier == "abcdef1"
    assert it.project == "aproxy-operator"
    assert it.state is None
    assert it.date == datetime(2026, 5, 14, 9, 0, tzinfo=timezone.utc)
