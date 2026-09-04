from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.discourse import DiscourseFetcher


def _config():
    return Config(
        identity={"discourse_base_url": "https://d.example.com", "discourse_username": "octo"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=[],
        main_projects=[],
        sources={"discourse": True},
    )


@responses.activate
def test_fetch_normalizes_actions(monkeypatch):
    monkeypatch.setenv("DISCOURSE_API_KEY", "k")
    responses.add(
        responses.GET,
        "https://d.example.com/user_actions.json",
        json={"user_actions": [{
            "title": "Announcing the aproxy charm",
            "created_at": "2026-05-01T00:00:00.000Z",
            "slug": "announcing-the-aproxy-charm",
            "topic_id": 42,
            "post_number": 1,
            "category_id": 7,
        }]},
        status=200,
    )
    items = DiscourseFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "discourse"
    assert it.title == "Announcing the aproxy charm"
    assert it.url == "https://d.example.com/t/announcing-the-aproxy-charm/42/1"
    assert it.date == datetime(2026, 5, 1, tzinfo=timezone.utc)
