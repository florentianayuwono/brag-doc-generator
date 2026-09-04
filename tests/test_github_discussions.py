from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_discussions import GithubDiscussionsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_discussions": True},
    )


@responses.activate
def test_fetch_normalizes_discussion(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={"data": {"search": {"nodes": [{
            "title": "How to configure aproxy",
            "url": "https://github.com/canonical/aproxy-operator/discussions/5",
            "number": 5,
            "createdAt": "2026-03-15T00:00:00Z",
            "repository": {"name": "aproxy-operator", "owner": {"login": "canonical"}},
        }]}}},
        status=200,
    )
    items = GithubDiscussionsFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_discussion"
    assert it.project == "aproxy-operator"
    assert it.identifier == "#5"
    assert it.role == "author"
    assert it.date == datetime(2026, 3, 15, tzinfo=timezone.utc)
