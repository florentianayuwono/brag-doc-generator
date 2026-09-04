from __future__ import annotations

import json
import sys

from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _warn(message: str) -> None:
    print(f"[bragdoc] {message}", file=sys.stderr)


def collect(config: Config, fetchers: list[Fetcher]) -> list[WorkItem]:
    items: list[WorkItem] = []
    for fetcher in fetchers:
        if not fetcher.enabled(config):
            _warn(f"skipping '{fetcher.name}' (disabled or missing token/config)")
            continue
        try:
            fetched = fetcher.fetch(config)
        except Exception as exc:  # noqa: BLE001 - isolate one source's failure
            _warn(f"'{fetcher.name}' failed: {exc}")
            continue
        for item in fetched:
            if config.window_start <= item.date <= config.window_end:
                items.append(item)
    return items


def write_cache(items: list[WorkItem], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([i.to_dict() for i in items], fh, indent=2)


def read_cache(path: str) -> list[WorkItem]:
    with open(path, "r", encoding="utf-8") as fh:
        return [WorkItem.from_dict(d) for d in json.load(fh)]
