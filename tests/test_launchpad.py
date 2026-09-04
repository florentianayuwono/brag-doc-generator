from datetime import datetime, timezone
from bragdoc.config import Config
from bragdoc.fetchers.launchpad import (
    LaunchpadFetcher, normalize_bug_task, normalize_merge_proposal,
)


def _config(enabled=True):
    return Config(
        identity={"launchpad_user": "octo"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=[],
        main_projects=[],
        sources={"launchpad": enabled},
    )


def test_enabled_toggle():
    assert LaunchpadFetcher().enabled(_config(enabled=False)) is False


def test_normalize_bug_task():
    raw = {
        "title": "Bug #1: crash on start",
        "web_link": "https://bugs.launchpad.net/foo/+bug/1",
        "status": "Fix Released",
        "date_created": "2026-03-01T00:00:00+00:00",
        "bug_target_name": "foo",
        "bug_id": 1,
    }
    it = normalize_bug_task(raw)
    assert it.source == "launchpad"
    assert it.project == "foo"
    assert it.identifier == "LP#1"
    assert it.state == "Fix Released"
    assert it.date == datetime(2026, 3, 1, tzinfo=timezone.utc)


def test_normalize_merge_proposal():
    raw = {
        "web_link": "https://code.launchpad.net/~octo/foo/+merge/42",
        "queue_status": "Merged",
        "date_created": "2026-04-01T00:00:00+00:00",
        "target_branch_name": "foo",
        "mp_id": 42,
        "description": "Add feature X",
    }
    it = normalize_merge_proposal(raw)
    assert it.source == "launchpad"
    assert it.project == "foo"
    assert it.identifier == "MP!42"
    assert it.state == "Merged"
    assert it.title == "Add feature X"
