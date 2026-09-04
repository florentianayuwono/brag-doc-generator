from __future__ import annotations

import re

from bragdoc.models import WorkItem

# Matches Jira-style issue keys, e.g. ISD-6136, PS-42
_ISSUE_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b")
# Matches a "[alias] rest of title" convention some teams use for Jira summaries
_BRACKET_RE = re.compile(r"^\[([^\]]+)\]")

_SUFFIXES = ("-operators", "-operator", "-charm", "-image-builder-operator")


def _aliases(project: str) -> set[str]:
    """Generate short aliases for a project name (e.g. strip common suffixes)."""
    lowered = project.lower()
    aliases = {lowered}
    for suffix in _SUFFIXES:
        if lowered.endswith(suffix):
            stripped = lowered[: -len(suffix)]
            if stripped:
                aliases.add(stripped)
    return aliases


def _issue_key_to_project(items: list[WorkItem]) -> dict[str, str]:
    """Map issue key -> project, based on non-Jira item titles that mention it."""
    mapping: dict[str, str] = {}
    for item in items:
        if item.source == "jira":
            continue
        for key in _ISSUE_KEY_RE.findall(item.title):
            mapping.setdefault(key, item.project)
    return mapping


def _alias_to_project(main_projects: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for project in main_projects:
        for alias in _aliases(project):
            mapping.setdefault(alias, project)
    return mapping


def _match_by_title(title: str, alias_map: dict[str, str]) -> str | None:
    title_lower = title.lower()
    bracket = _BRACKET_RE.match(title)
    candidates = [bracket.group(1).lower()] if bracket else []
    candidates.append(title_lower)
    # Try longer/more specific aliases first to avoid partial false positives.
    for alias in sorted(alias_map, key=len, reverse=True):
        for candidate in candidates:
            if alias and alias in candidate:
                return alias_map[alias]
    return None


def link_jira_projects(items: list[WorkItem], main_projects: list[str]) -> list[WorkItem]:
    """Re-assign Jira WorkItems' `project` to match their related GitHub repo.

    Priority order:
    1. `extra["linked_repo"]` (from Jira's Development panel / dev-status API),
       if it names one of the configured main_projects.
    2. The Jira issue key appearing in a GitHub PR/commit title in this batch.
    3. The Jira title matching a project alias (bracketed prefix or substring).
    """
    key_to_project = _issue_key_to_project(items)
    alias_map = _alias_to_project(main_projects)

    linked: list[WorkItem] = []
    for item in items:
        if item.source != "jira":
            linked.append(item)
            continue

        linked_repo = item.extra.get("linked_repo")
        if linked_repo and linked_repo in main_projects:
            item.project = linked_repo
        elif item.identifier in key_to_project:
            item.project = key_to_project[item.identifier]
        else:
            matched = _match_by_title(item.title, alias_map)
            if matched:
                item.project = matched
        linked.append(item)
    return linked
