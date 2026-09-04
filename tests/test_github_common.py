from datetime import datetime, timezone
from bragdoc.fetchers import _github_common as gh


def test_org_qualifier():
    assert gh.org_qualifier(["a", "b"]) == "org:a org:b"
    assert gh.org_qualifier([]) == ""


def test_parse_repo():
    org, repo = gh.parse_repo("https://api.github.com/repos/canonical/aproxy-operator")
    assert (org, repo) == ("canonical", "aproxy-operator")


def test_parse_ts():
    dt = gh.parse_ts("2026-05-14T09:30:00Z")
    assert dt == datetime(2026, 5, 14, 9, 30, tzinfo=timezone.utc)


def test_pick_issue_date_prefers_merged_then_closed_then_created():
    merged = {"created_at": "2026-01-01T00:00:00Z", "closed_at": "2026-02-01T00:00:00Z",
              "pull_request": {"merged_at": "2026-03-01T00:00:00Z"}}
    assert gh.pick_issue_date(merged) == gh.parse_ts("2026-03-01T00:00:00Z")
    closed = {"created_at": "2026-01-01T00:00:00Z", "closed_at": "2026-02-01T00:00:00Z"}
    assert gh.pick_issue_date(closed) == gh.parse_ts("2026-02-01T00:00:00Z")
    open_ = {"created_at": "2026-01-01T00:00:00Z", "closed_at": None}
    assert gh.pick_issue_date(open_) == gh.parse_ts("2026-01-01T00:00:00Z")


def test_issue_state():
    assert gh.issue_state({"state": "closed", "pull_request": {"merged_at": "x"}}) == "merged"
    assert gh.issue_state({"state": "closed", "pull_request": {"merged_at": None}}) == "closed"
    assert gh.issue_state({"state": "open"}) == "open"


def test_search_issues_paginates(responses_mock=None):
    import responses

    @responses.activate
    def run():
        page1 = {"items": [{"id": i} for i in range(100)]}
        page2 = {"items": [{"id": 100}]}
        responses.add(responses.GET, "https://api.github.com/search/issues",
                      json=page1, status=200)
        responses.add(responses.GET, "https://api.github.com/search/issues",
                      json=page2, status=200)
        out = gh.search_issues("author:x", token="t")
        assert len(out) == 101

    run()
