from bragdoc.fetchers.registry import all_fetchers


def test_registry_lists_all_eight_sources():
    names = {f.name for f in all_fetchers()}
    assert names == {
        "github_prs", "github_reviews", "github_issues", "github_commits",
        "github_discussions", "jira", "discourse", "launchpad",
    }
