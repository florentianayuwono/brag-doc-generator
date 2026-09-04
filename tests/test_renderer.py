from datetime import datetime, timezone
from bragdoc.renderer import render_markdown
from bragdoc.models import WorkItem


def _item(source, project, role, identifier, state="merged",
          date=datetime(2026, 5, 1, tzinfo=timezone.utc)):
    return WorkItem(source, project, "canonical", f"title-{identifier}",
                    f"https://x/{identifier}", date, role, state, identifier, {})


def test_render_groups_projects_and_collaboration():
    items = [
        _item("github_pr", "aproxy-operator", "author", "#1"),
        _item("github_review", "nginx", "reviewer", "#2"),
        _item("github_pr", "some-other-repo", "author", "#3"),
    ]
    md = render_markdown(items, main_projects=["aproxy-operator"],
                         username="octo",
                         window=(datetime(2026, 3, 1, tzinfo=timezone.utc),
                                 datetime(2026, 9, 1, tzinfo=timezone.utc)))
    assert "# Brag Digest" in md
    assert "## Projects" in md
    assert "### aproxy-operator" in md
    assert "## Cross-team & collaboration" in md
    # main-project authored item under Projects
    proj_section = md.split("## Projects")[1].split("## Cross-team")[0]
    assert "#1" in proj_section
    # reviewer item and non-main authored item under collaboration
    collab_section = md.split("## Cross-team & collaboration")[1]
    assert "#2" in collab_section
    assert "#3" in collab_section


def test_render_includes_summary_counts():
    items = [
        _item("github_pr", "aproxy-operator", "author", "#1"),
        _item("github_review", "nginx", "reviewer", "#2"),
    ]
    md = render_markdown(items, main_projects=["aproxy-operator"], username="octo",
                         window=(datetime(2026, 3, 1, tzinfo=timezone.utc),
                                 datetime(2026, 9, 1, tzinfo=timezone.utc)))
    assert "## Summary" in md
    assert "PRs" in md
