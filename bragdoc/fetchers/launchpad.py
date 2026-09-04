from __future__ import annotations

import os
from datetime import datetime

from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_bug_task(raw: dict) -> WorkItem:
    return WorkItem(
        source="launchpad",
        project=raw["bug_target_name"],
        org=None,
        title=raw["title"],
        url=raw["web_link"],
        date=_parse_ts(raw["date_created"]),
        role="author",
        state=raw["status"],
        identifier=f"LP#{raw['bug_id']}",
        extra={"kind": "bug"},
    )


def normalize_merge_proposal(raw: dict) -> WorkItem:
    return WorkItem(
        source="launchpad",
        project=raw["target_branch_name"],
        org=None,
        title=raw.get("description") or raw["web_link"],
        url=raw["web_link"],
        date=_parse_ts(raw["date_created"]),
        role="author",
        state=raw["queue_status"],
        identifier=f"MP!{raw['mp_id']}",
        extra={"kind": "merge_proposal"},
    )


class LaunchpadFetcher(Fetcher):
    name = "launchpad"

    def enabled(self, config: Config) -> bool:
        if not config.source_enabled(self.name):
            return False
        if not config.identity.get("launchpad_user"):
            return False
        try:
            import launchpadlib  # noqa: F401
        except ImportError:
            return False
        return True

    def fetch(self, config: Config) -> list[WorkItem]:
        from launchpadlib.launchpad import Launchpad

        cred = os.environ.get("LAUNCHPAD_CREDENTIALS")
        lp = Launchpad.login_with(
            "bragdoc", "production", credentials_file=cred
        ) if cred else Launchpad.login_anonymously("bragdoc", "production")
        user = lp.people[config.identity["launchpad_user"]]
        out: list[WorkItem] = []
        for task in user.searchTasks(assignee=user):
            out.append(normalize_bug_task({
                "title": task.title,
                "web_link": task.web_link,
                "status": task.status,
                "date_created": task.date_created.isoformat(),
                "bug_target_name": task.bug_target_name,
                "bug_id": task.bug.id,
            }))
        for mp in user.getMergeProposals():
            out.append(normalize_merge_proposal({
                "web_link": mp.web_link,
                "queue_status": mp.queue_status,
                "date_created": mp.date_created.isoformat(),
                "target_branch_name": getattr(mp.target_branch, "name", ""),
                "mp_id": mp.self_link.rstrip("/").split("/")[-1],
                "description": mp.description,
            }))
        return out
