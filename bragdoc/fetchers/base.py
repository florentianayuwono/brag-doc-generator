from __future__ import annotations

from abc import ABC, abstractmethod

from bragdoc.config import Config
from bragdoc.models import WorkItem


class Fetcher(ABC):
    name: str = "base"

    @abstractmethod
    def enabled(self, config: Config) -> bool:
        ...

    @abstractmethod
    def fetch(self, config: Config) -> list[WorkItem]:
        ...
