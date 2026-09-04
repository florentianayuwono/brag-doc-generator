from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.jira import JiraFetcher


def _config():
    return Config(
        identity={"jira_email": "me@example.com", "jira_server": "https://ex.atlassian.net"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=[],
        main_projects=[],
        sources={"jira": True},
    )


def test_enabled_requires_token(monkeypatch):
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    assert JiraFetcher().enabled(_config()) is False
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    assert JiraFetcher().enabled(_config()) is True


@responses.activate
def test_fetch_normalizes_issue(monkeypatch):
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://ex.atlassian.net/rest/api/3/search",
        json={"issues": [{
            "key": "PS-456",
            "fields": {
                "summary": "Aproxy subordinate charm spec",
                "status": {"name": "Done"},
                "updated": "2026-04-10T12:00:00.000+0000",
                "project": {"key": "PS"},
            },
        }], "total": 1, "startAt": 0, "maxResults": 50},
        status=200,
    )
    items = JiraFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "jira"
    assert it.project == "PS"
    assert it.identifier == "PS-456"
    assert it.state == "Done"
    assert it.url == "https://ex.atlassian.net/browse/PS-456"
    assert it.date == datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc)
