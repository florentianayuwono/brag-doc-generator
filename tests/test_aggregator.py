from datetime import datetime, timezone
from bragdoc.aggregator import collect, write_cache, read_cache
from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _config():
    return Config(
        identity={}, window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 1, tzinfo=timezone.utc),
        github_orgs=[], main_projects=[], sources={},
    )


def _item(date):
    return WorkItem("github_pr", "repo", "canonical", "t", "u", date,
                    "author", "merged", "#1", {})


class GoodFetcher(Fetcher):
    name = "good"

    def enabled(self, config):
        return True

    def fetch(self, config):
        return [
            _item(datetime(2026, 5, 1, tzinfo=timezone.utc)),   # in window
            _item(datetime(2026, 1, 1, tzinfo=timezone.utc)),   # before window
        ]


class DisabledFetcher(Fetcher):
    name = "disabled"

    def enabled(self, config):
        return False

    def fetch(self, config):
        raise AssertionError("must not be called")


class BrokenFetcher(Fetcher):
    name = "broken"

    def enabled(self, config):
        return True

    def fetch(self, config):
        raise RuntimeError("boom")


def test_collect_filters_window_and_skips_disabled_and_broken():
    items = collect(_config(), [GoodFetcher(), DisabledFetcher(), BrokenFetcher()])
    assert len(items) == 1
    assert items[0].date == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_cache_roundtrip(tmp_path):
    path = tmp_path / "cache.json"
    items = [_item(datetime(2026, 5, 1, tzinfo=timezone.utc))]
    write_cache(items, str(path))
    restored = read_cache(str(path))
    assert restored == items


def test_collect_links_jira_items_to_related_github_project():
    def _gh_item():
        return WorkItem("github_pr", "aproxy-operator", "canonical",
                        "feat: fix things (PS-1)", "u",
                        datetime(2026, 5, 1, tzinfo=timezone.utc),
                        "author", "merged", "#1", {})

    def _jira_item():
        return WorkItem("jira", "PS", None, "fix things", "u",
                        datetime(2026, 5, 2, tzinfo=timezone.utc),
                        "author", "Done", "PS-1", {})

    class GithubFetcher(Fetcher):
        name = "github"

        def enabled(self, config):
            return True

        def fetch(self, config):
            return [_gh_item()]

    class JiraFetcher(Fetcher):
        name = "jira"

        def enabled(self, config):
            return True

        def fetch(self, config):
            return [_jira_item()]

    config = Config(
        identity={}, window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 1, tzinfo=timezone.utc),
        github_orgs=[], main_projects=["aproxy-operator"], sources={},
    )
    items = collect(config, [GithubFetcher(), JiraFetcher()])
    jira_result = [i for i in items if i.source == "jira"][0]
    assert jira_result.project == "aproxy-operator"
