from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import yaml
from dotenv import load_dotenv


@dataclass
class Config:
    identity: dict
    window_start: datetime
    window_end: datetime
    github_orgs: list[str]
    main_projects: list[str]
    sources: dict
    goals: dict = field(default_factory=dict)

    def source_enabled(self, name: str) -> bool:
        return bool(self.sources.get(name, False))


def _parse_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _window(date_range: dict) -> tuple[datetime, datetime]:
    if date_range.get("start") and date_range.get("end"):
        return _parse_iso(str(date_range["start"])), _parse_iso(str(date_range["end"]))
    months = int(date_range.get("months_back", 6))
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=months * 30)
    return start, end


def load_config(config_path: str = "config.yaml", env_path: str = ".env") -> Config:
    load_dotenv(env_path)
    with open(config_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    start, end = _window(raw.get("date_range", {}))
    scope = raw.get("scope", {})
    return Config(
        identity=raw.get("identity", {}),
        window_start=start,
        window_end=end,
        github_orgs=list(scope.get("github_orgs", [])),
        main_projects=list(scope.get("main_projects", [])),
        sources=raw.get("sources", {}),
        goals=raw.get("goals", {}),
    )
