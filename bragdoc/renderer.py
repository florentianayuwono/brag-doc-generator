from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from bragdoc.models import WorkItem

_SOURCE_LABELS = {
    "github_pr": "PRs authored",
    "github_review": "PRs reviewed",
    "github_issue": "issues",
    "github_commit": "commits",
    "github_discussion": "discussions",
    "jira": "Jira",
    "discourse": "Discourse",
    "launchpad": "Launchpad",
}


def _is_collaboration(item: WorkItem, main_projects: list[str]) -> bool:
    if item.role == "reviewer":
        return True
    return item.project not in main_projects


def _bullet(item: WorkItem) -> str:
    prefix = "Reviewed: " if item.role == "reviewer" else ""
    state = f" · {item.state}" if item.state else ""
    date = item.date.date().isoformat()
    return (f"- **{prefix}{item.title}** — {item.identifier}{state} · "
            f"{date} · {item.url}")


def _render_group(items: list[WorkItem]) -> list[str]:
    lines: list[str] = []
    by_repo: dict[str, list[WorkItem]] = defaultdict(list)
    for item in items:
        by_repo[item.project].append(item)
    for repo in sorted(by_repo):
        lines.append(f"### {repo}")
        for item in sorted(by_repo[repo], key=lambda i: i.date, reverse=True):
            lines.append(_bullet(item))
        lines.append("")
    return lines


def _summary(items: list[WorkItem]) -> str:
    counts = Counter(i.source for i in items)
    parts = [f"{counts[src]} {label}" for src, label in _SOURCE_LABELS.items()
             if counts.get(src)]
    return " · ".join(parts) if parts else "No items found."


def render_markdown(items: list[WorkItem], main_projects: list[str],
                    username: str, window: tuple[datetime, datetime]) -> str:
    start, end = window
    projects = [i for i in items if not _is_collaboration(i, main_projects)]
    collab = [i for i in items if _is_collaboration(i, main_projects)]

    lines = [
        f"# Brag Digest — {username}",
        f"Window: {start.date()} → {end.date()} · "
        f"Generated {datetime.now().date()}",
        "",
        "## Summary",
        _summary(items),
        "",
        "## Projects",
    ]
    lines += _render_group(projects) if projects else ["_No project work found._", ""]
    lines.append("## Cross-team & collaboration")
    lines += _render_group(collab) if collab else ["_No collaboration items found._", ""]
    return "\n".join(lines).rstrip() + "\n"
