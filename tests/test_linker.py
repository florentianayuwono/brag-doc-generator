from datetime import datetime, timezone
from bragdoc.linker import link_jira_projects
from bragdoc.models import WorkItem


def _gh(title, project, identifier="#1"):
    return WorkItem("github_pr", project, "canonical", title, "https://x", 
                    datetime(2026, 5, 1, tzinfo=timezone.utc), "author", "merged",
                    identifier, {})


def _jira(title, identifier, project="ISD", extra=None):
    return WorkItem("jira", project, None, title, "https://x/browse/" + identifier,
                    datetime(2026, 5, 1, tzinfo=timezone.utc), "author", "Done",
                    identifier, extra or {})


def test_links_via_dev_status_extra_when_repo_matches_main_project():
    items = [
        _jira("Some unrelated title", "ISD-1",
              extra={"linked_repo": "content-cache-operator"}),
    ]
    linked = link_jira_projects(items, main_projects=["content-cache-operator"])
    assert linked[0].project == "content-cache-operator"


def test_links_via_issue_key_mentioned_in_github_title():
    items = [
        _gh("feat: support cache-config relation (ISD-6136)",
            "ingress-configurator-operator"),
        _jira("[ingress-configurator] support cache-config relation", "ISD-6136"),
    ]
    linked = link_jira_projects(items, main_projects=["ingress-configurator-operator"])
    jira_item = [i for i in linked if i.source == "jira"][0]
    assert jira_item.project == "ingress-configurator-operator"


def test_links_via_bracketed_title_alias_when_no_other_signal():
    items = [
        _jira("[content-cache] optimize backend fetches", "ISD-9999"),
    ]
    linked = link_jira_projects(items, main_projects=["content-cache-operator"])
    assert linked[0].project == "content-cache-operator"


def test_links_via_substring_alias_in_title_without_brackets():
    items = [
        _jira("Improve github-runner-operators observability", "ISD-42"),
    ]
    linked = link_jira_projects(items, main_projects=["github-runner-operators"])
    assert linked[0].project == "github-runner-operators"


def test_no_match_leaves_project_unchanged():
    items = [_jira("Completely unrelated ticket", "PS-1", project="PS")]
    linked = link_jira_projects(items, main_projects=["content-cache-operator"])
    assert linked[0].project == "PS"


def test_non_jira_items_are_untouched():
    items = [_gh("some pr", "some-repo")]
    linked = link_jira_projects(items, main_projects=["some-repo"])
    assert linked[0].project == "some-repo"
