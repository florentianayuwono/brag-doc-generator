from __future__ import annotations

import os
from datetime import datetime

import requests

from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem

# Discourse user_action_type: 4 = new topic, 5 = reply
_ACTION_FILTER = "4,5"


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class DiscourseFetcher(Fetcher):
    name = "discourse"

    def enabled(self, config: Config) -> bool:
        has_cfg = bool(config.identity.get("discourse_username")) and \
            bool(config.identity.get("discourse_base_url"))
        return config.source_enabled(self.name) and \
            os.environ.get("DISCOURSE_API_KEY") is not None and has_cfg

    def fetch(self, config: Config) -> list[WorkItem]:
        base = config.identity["discourse_base_url"].rstrip("/")
        username = config.identity["discourse_username"]
        headers = {
            "Api-Key": os.environ["DISCOURSE_API_KEY"],
            "Api-Username": username,
        }
        resp = requests.get(
            f"{base}/user_actions.json",
            params={"username": username, "filter": _ACTION_FILTER, "offset": 0},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        out: list[WorkItem] = []
        for act in resp.json().get("user_actions", []):
            slug = act.get("slug", "")
            topic_id = act.get("topic_id", "")
            post_number = act.get("post_number", 1)
            out.append(WorkItem(
                source="discourse",
                project=f"category:{act.get('category_id')}",
                org=None,
                title=act["title"],
                url=f"{base}/t/{slug}/{topic_id}/{post_number}",
                date=_parse_ts(act["created_at"]),
                role="author",
                state=None,
                identifier=f"topic:{topic_id}",
                extra={},
            ))
        return out
