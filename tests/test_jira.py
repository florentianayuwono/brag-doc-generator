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


def test_enabled_treats_empty_token_as_missing(monkeypatch):
    monkeypatch.setenv("JIRA_API_TOKEN", "")
    assert JiraFetcher().enabled(_config()) is False


@responses.activate
def test_fetch_normalizes_issue(monkeypatch):
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    responses.add(
        responses.POST,
        "https://ex.atlassian.net/rest/api/3/search/jql",
        json={"issues": [{
            "key": "PS-456",
            "fields": {
                "summary": "Aproxy subordinate charm spec",
                "status": {"name": "Done"},
                "updated": "2026-04-10T12:00:00.000+0000",
                "project": {"key": "PS"},
            },
        }], "isLast": True},
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


@responses.activate
def test_fetch_paginates_with_next_page_token(monkeypatch):
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    responses.add(
        responses.POST,
        "https://ex.atlassian.net/rest/api/3/search/jql",
        json={"issues": [{
            "key": "PS-1",
            "fields": {
                "summary": "First page issue",
                "status": {"name": "Done"},
                "updated": "2026-04-10T12:00:00.000+0000",
                "project": {"key": "PS"},
            },
        }], "isLast": False, "nextPageToken": "abc"},
        status=200,
    )
    responses.add(
        responses.POST,
        "https://ex.atlassian.net/rest/api/3/search/jql",
        json={"issues": [{
            "key": "PS-2",
            "fields": {
                "summary": "Second page issue",
                "status": {"name": "Done"},
                "updated": "2026-04-11T12:00:00.000+0000",
                "project": {"key": "PS"},
            },
        }], "isLast": True},
        status=200,
    )
    items = JiraFetcher().fetch(_config())
    assert [i.identifier for i in items] == ["PS-1", "PS-2"]
    second_call_body = responses.calls[1].request.body
    assert b'"abc"' in second_call_body
