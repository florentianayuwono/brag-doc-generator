from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_prs import GithubPrsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=["aproxy-operator"],
        sources={"github_prs": True},
    )


def test_enabled_requires_toggle_and_token(monkeypatch):
    f = GithubPrsFetcher()
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert f.enabled(_config()) is False
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert f.enabled(_config()) is True


@responses.activate
def test_fetch_normalizes(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": [{
            "title": "Add PS7 support",
            "html_url": "https://github.com/canonical/aproxy-operator/pull/123",
            "number": 123,
            "state": "closed",
            "created_at": "2026-05-10T00:00:00Z",
            "closed_at": "2026-05-14T00:00:00Z",
            "repository_url": "https://api.github.com/repos/canonical/aproxy-operator",
            "pull_request": {"merged_at": "2026-05-14T00:00:00Z"},
        }]},
        status=200,
    )
    items = GithubPrsFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_pr"
    assert it.project == "aproxy-operator"
    assert it.org == "canonical"
    assert it.role == "author"
    assert it.state == "merged"
    assert it.identifier == "#123"
    assert it.date == datetime(2026, 5, 14, tzinfo=timezone.utc)
