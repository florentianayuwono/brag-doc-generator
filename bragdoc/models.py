from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkItem:
    source: str
    project: str
    org: str | None
    title: str
    url: str
    date: datetime
    role: str
    state: str | None
    identifier: str
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "project": self.project,
            "org": self.org,
            "title": self.title,
            "url": self.url,
            "date": self.date.isoformat(),
            "role": self.role,
            "state": self.state,
            "identifier": self.identifier,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorkItem":
        return cls(
            source=d["source"],
            project=d["project"],
            org=d.get("org"),
            title=d["title"],
            url=d["url"],
            date=datetime.fromisoformat(d["date"]),
            role=d["role"],
            state=d.get("state"),
            identifier=d["identifier"],
            extra=d.get("extra", {}),
        )
