# Brag Doc Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that fetches a user's GitHub, Jira, Discourse, and Launchpad activity over a configurable window and renders an organized Markdown "brag digest" grouped by project + collaboration.

**Architecture:** Modular package. Each source is an isolated fetcher returning a common `WorkItem`. An aggregator runs enabled fetchers, filters to the date window, and writes a JSON cache. A renderer reads the cache and emits Markdown. `fetch` (network) and `render` (offline) are separate CLI commands.

**Tech Stack:** Python 3.12, `requests` (GitHub REST + GraphQL, Jira REST, Discourse), `launchpadlib` (optional, Launchpad), `PyYAML`, `python-dotenv`. Tests with `pytest` + `responses`.

---

## File Structure

- `pyproject.toml` — package metadata + deps + console entrypoint `bragdoc`.
- `.gitignore` — ignore `.env`, `cache/`, `output/`, `__pycache__`, `*.egg-info`, `.venv`.
- `.env.example` — secret env var template.
- `config.example.yaml` — non-secret settings template.
- `bragdoc/__init__.py` — package marker + version.
- `bragdoc/models.py` — `WorkItem` dataclass + JSON (de)serialization.
- `bragdoc/config.py` — `Config` dataclass + `load_config()`.
- `bragdoc/fetchers/base.py` — `Fetcher` ABC.
- `bragdoc/fetchers/_github_common.py` — shared GitHub REST/GraphQL helpers.
- `bragdoc/fetchers/github_prs.py` — PRs authored.
- `bragdoc/fetchers/github_reviews.py` — PRs reviewed.
- `bragdoc/fetchers/github_issues.py` — issues authored.
- `bragdoc/fetchers/github_commits.py` — commits authored.
- `bragdoc/fetchers/github_discussions.py` — discussions authored (GraphQL).
- `bragdoc/fetchers/jira.py` — Jira issues.
- `bragdoc/fetchers/discourse.py` — Discourse topics/posts.
- `bragdoc/fetchers/launchpad.py` — Launchpad bugs + merge proposals.
- `bragdoc/fetchers/registry.py` — list of all fetcher instances.
- `bragdoc/aggregator.py` — run fetchers, window-filter, cache read/write.
- `bragdoc/renderer.py` — group + render Markdown.
- `bragdoc/cli.py` — argparse entrypoint (`fetch` / `render` / `run`).
- `tests/…` — one test module per component.

Note (deviation from spec): a private `_github_common.py` helper and a `registry.py` are added under `fetchers/` to keep GitHub fetchers DRY and to list fetchers in one place. Both are internal implementation details consistent with the spec's modular intent.

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `config.example.yaml`
- Create: `bragdoc/__init__.py`
- Create: `bragdoc/fetchers/__init__.py`
- Create: `tests/__init__.py`
- Test: `tests/test_smoke.py`

- [ ] **Step 1: Write the failing test**

`tests/test_smoke.py`:
```python
def test_package_imports():
    import bragdoc
    assert bragdoc.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bragdoc'`

- [ ] **Step 3: Create scaffold files**

`pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "bragdoc"
version = "0.1.0"
description = "Generate an organized brag digest from GitHub, Jira, Discourse, and Launchpad activity."
requires-python = ">=3.10"
dependencies = [
    "requests>=2.31",
    "PyYAML>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
launchpad = ["launchpadlib>=1.11"]
dev = ["pytest>=8.0", "responses>=0.25"]

[project.scripts]
bragdoc = "bragdoc.cli:main"

[tool.setuptools.packages.find]
include = ["bragdoc*"]
```

`.gitignore`:
```
.env
cache/
output/
__pycache__/
*.egg-info/
.venv/
.pytest_cache/
```

`.env.example`:
```
GITHUB_TOKEN=
JIRA_API_TOKEN=
DISCOURSE_API_KEY=
LAUNCHPAD_CREDENTIALS=
```

`config.example.yaml`:
```yaml
identity:
  github_username: florentianayuwono
  jira_email: florentiana.yuwono@canonical.com
  jira_server: https://warthogs.atlassian.net
  discourse_base_url: https://discourse.canonical.com
  discourse_username: florenyu
  launchpad_user: florenyu

date_range:
  months_back: 6
  # start: "2026-03-04"   # optional explicit ISO date overrides months_back
  # end: "2026-09-04"

scope:
  github_orgs: [canonical]
  main_projects:
    - github-actions-runner
    - github-runner-image-builder-operator
    - github-runner-operators
    - github-runner-operator
    - content-cache-operator
    - ingress-configurator-operator

sources:
  github_prs: true
  github_reviews: true
  github_issues: true
  github_commits: true
  github_discussions: true
  jira: true
  discourse: true
  launchpad: true
```

`bragdoc/__init__.py`:
```python
__version__ = "0.1.0"
```

`bragdoc/fetchers/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: Install dev deps and run test to verify it passes**

Run: `pip install -e '.[dev]' && python -m pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold bragdoc package"
```

---

### Task 2: WorkItem model

**Files:**
- Create: `bragdoc/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
from datetime import datetime, timezone
from bragdoc.models import WorkItem


def _item():
    return WorkItem(
        source="github_pr",
        project="aproxy-operator",
        org="canonical",
        title="Add PS7 support",
        url="https://github.com/canonical/aproxy-operator/pull/123",
        date=datetime(2026, 5, 14, tzinfo=timezone.utc),
        role="author",
        state="merged",
        identifier="#123",
        extra={"additions": 10},
    )


def test_roundtrip_json():
    item = _item()
    restored = WorkItem.from_dict(item.to_dict())
    assert restored == item


def test_date_serializes_to_iso():
    d = _item().to_dict()
    assert d["date"] == "2026-05-14T00:00:00+00:00"
    assert isinstance(d["extra"], dict)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bragdoc.models'`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/models.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/models.py tests/test_models.py
git commit -m "feat: add WorkItem model with JSON serialization"
```

---

### Task 3: Config loader

**Files:**
- Create: `bragdoc/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
from datetime import datetime
from bragdoc.config import Config, load_config

CONFIG_YAML = """
identity:
  github_username: octocat
  jira_email: me@example.com
  jira_server: https://example.atlassian.net
  discourse_base_url: https://discourse.example.com
  discourse_username: octo
  launchpad_user: octo
date_range:
  months_back: 6
scope:
  github_orgs: [acme]
  main_projects: [widget]
sources:
  github_prs: true
  jira: false
"""


def _write(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CONFIG_YAML)
    env = tmp_path / ".env"
    env.write_text("GITHUB_TOKEN=abc\n")
    return cfg, env


def test_load_config_parses_identity_and_scope(tmp_path):
    cfg, env = _write(tmp_path)
    c = load_config(str(cfg), str(env))
    assert c.identity["github_username"] == "octocat"
    assert c.github_orgs == ["acme"]
    assert c.main_projects == ["widget"]


def test_window_from_months_back(tmp_path):
    cfg, env = _write(tmp_path)
    c = load_config(str(cfg), str(env))
    span_days = (c.window_end - c.window_start).days
    assert 170 <= span_days <= 190  # ~6 months


def test_explicit_dates_override(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CONFIG_YAML.replace(
        "  months_back: 6",
        '  months_back: 6\n  start: "2026-01-01"\n  end: "2026-02-01"',
    ))
    env = tmp_path / ".env"
    env.write_text("")
    c = load_config(str(cfg), str(env))
    assert c.window_start == datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    assert c.window_end == datetime.fromisoformat("2026-02-01T00:00:00+00:00")


def test_source_enabled_requires_toggle(tmp_path):
    cfg, env = _write(tmp_path)
    c = load_config(str(cfg), str(env))
    assert c.source_enabled("github_prs") is True
    assert c.source_enabled("jira") is False
    assert c.source_enabled("discourse") is False  # absent -> default False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bragdoc.config'`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/config.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
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
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/config.py tests/test_config.py
git commit -m "feat: add config loader with date window and source toggles"
```

---

### Task 4: Fetcher base class

**Files:**
- Create: `bragdoc/fetchers/base.py`
- Test: `tests/test_base.py`

- [ ] **Step 1: Write the failing test**

`tests/test_base.py`:
```python
import pytest
from bragdoc.fetchers.base import Fetcher


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        Fetcher()


def test_subclass_contract():
    class Dummy(Fetcher):
        name = "dummy"

        def enabled(self, config):
            return True

        def fetch(self, config):
            return []

    d = Dummy()
    assert d.name == "dummy"
    assert d.enabled(None) is True
    assert d.fetch(None) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_base.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bragdoc.fetchers.base'`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/base.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_base.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/base.py tests/test_base.py
git commit -m "feat: add Fetcher abstract base class"
```

---

### Task 5: Shared GitHub helpers

**Files:**
- Create: `bragdoc/fetchers/_github_common.py`
- Test: `tests/test_github_common.py`

- [ ] **Step 1: Write the failing test**

`tests/test_github_common.py`:
```python
from datetime import datetime, timezone
from bragdoc.fetchers import _github_common as gh


def test_org_qualifier():
    assert gh.org_qualifier(["a", "b"]) == "org:a org:b"
    assert gh.org_qualifier([]) == ""


def test_parse_repo():
    org, repo = gh.parse_repo("https://api.github.com/repos/canonical/aproxy-operator")
    assert (org, repo) == ("canonical", "aproxy-operator")


def test_parse_ts():
    dt = gh.parse_ts("2026-05-14T09:30:00Z")
    assert dt == datetime(2026, 5, 14, 9, 30, tzinfo=timezone.utc)


def test_pick_issue_date_prefers_merged_then_closed_then_created():
    merged = {"created_at": "2026-01-01T00:00:00Z", "closed_at": "2026-02-01T00:00:00Z",
              "pull_request": {"merged_at": "2026-03-01T00:00:00Z"}}
    assert gh.pick_issue_date(merged) == gh.parse_ts("2026-03-01T00:00:00Z")
    closed = {"created_at": "2026-01-01T00:00:00Z", "closed_at": "2026-02-01T00:00:00Z"}
    assert gh.pick_issue_date(closed) == gh.parse_ts("2026-02-01T00:00:00Z")
    open_ = {"created_at": "2026-01-01T00:00:00Z", "closed_at": None}
    assert gh.pick_issue_date(open_) == gh.parse_ts("2026-01-01T00:00:00Z")


def test_issue_state():
    assert gh.issue_state({"state": "closed", "pull_request": {"merged_at": "x"}}) == "merged"
    assert gh.issue_state({"state": "closed", "pull_request": {"merged_at": None}}) == "closed"
    assert gh.issue_state({"state": "open"}) == "open"


def test_search_issues_paginates(responses_mock=None):
    import responses

    @responses.activate
    def run():
        page1 = {"items": [{"id": i} for i in range(100)]}
        page2 = {"items": [{"id": 100}]}
        responses.add(responses.GET, "https://api.github.com/search/issues",
                      json=page1, status=200)
        responses.add(responses.GET, "https://api.github.com/search/issues",
                      json=page2, status=200)
        out = gh.search_issues("author:x", token="t")
        assert len(out) == 101

    run()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_common.py -v`
Expected: FAIL with `ImportError` / `AttributeError` (module or functions missing)

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/_github_common.py`:
```python
from __future__ import annotations

import os
from datetime import datetime

import requests

API = "https://api.github.com"


def github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN")


def _headers(token: str | None) -> dict:
    token = token or github_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def org_qualifier(orgs: list[str]) -> str:
    return " ".join(f"org:{o}" for o in orgs)


def parse_repo(repository_url: str) -> tuple[str, str]:
    parts = repository_url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def pick_issue_date(item: dict) -> datetime:
    pr = item.get("pull_request") or {}
    if pr.get("merged_at"):
        return parse_ts(pr["merged_at"])
    if item.get("closed_at"):
        return parse_ts(item["closed_at"])
    return parse_ts(item["created_at"])


def issue_state(item: dict) -> str:
    pr = item.get("pull_request")
    if pr is not None:
        return "merged" if pr.get("merged_at") else item.get("state", "open")
    return item.get("state", "open")


def search_issues(query: str, token: str | None = None) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        resp = requests.get(
            f"{API}/search/issues",
            headers=_headers(token),
            params={"q": query, "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json().get("items", [])
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_common.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/_github_common.py tests/test_github_common.py
git commit -m "feat: add shared GitHub REST helpers"
```

---

### Task 6: GitHub PRs authored fetcher

**Files:**
- Create: `bragdoc/fetchers/github_prs.py`
- Test: `tests/test_github_prs.py`

- [ ] **Step 1: Write the failing test**

`tests/test_github_prs.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_prs import GithubPrsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=["aproxy-operator"],
        sources={"github_prs": True},
    )


def test_enabled_requires_toggle_and_token(monkeypatch):
    f = GithubPrsFetcher()
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert f.enabled(_config()) is False
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert f.enabled(_config()) is True


@responses.activate
def test_fetch_normalizes(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": [{
            "title": "Add PS7 support",
            "html_url": "https://github.com/canonical/aproxy-operator/pull/123",
            "number": 123,
            "state": "closed",
            "created_at": "2026-05-10T00:00:00Z",
            "closed_at": "2026-05-14T00:00:00Z",
            "repository_url": "https://api.github.com/repos/canonical/aproxy-operator",
            "pull_request": {"merged_at": "2026-05-14T00:00:00Z"},
        }]},
        status=200,
    )
    items = GithubPrsFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_pr"
    assert it.project == "aproxy-operator"
    assert it.org == "canonical"
    assert it.role == "author"
    assert it.state == "merged"
    assert it.identifier == "#123"
    assert it.date == datetime(2026, 5, 14, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_prs.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bragdoc.fetchers.github_prs'`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/github_prs.py`:
```python
from __future__ import annotations

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


class GithubPrsFetcher(Fetcher):
    name = "github_prs"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        query = f"author:{user} type:pr updated:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            query += f" {orgs}"
        out: list[WorkItem] = []
        for item in gh.search_issues(query):
            org, repo = gh.parse_repo(item["repository_url"])
            out.append(WorkItem(
                source="github_pr",
                project=repo,
                org=org,
                title=item["title"],
                url=item["html_url"],
                date=gh.pick_issue_date(item),
                role="author",
                state=gh.issue_state(item),
                identifier=f"#{item['number']}",
                extra={},
            ))
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_prs.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/github_prs.py tests/test_github_prs.py
git commit -m "feat: add GitHub PRs-authored fetcher"
```

---

### Task 7: GitHub PRs reviewed fetcher

**Files:**
- Create: `bragdoc/fetchers/github_reviews.py`
- Test: `tests/test_github_reviews.py`

- [ ] **Step 1: Write the failing test**

`tests/test_github_reviews.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_reviews import GithubReviewsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_reviews": True},
    )


@responses.activate
def test_fetch_excludes_self_authored(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": [
            {
                "title": "fix ingress bug",
                "html_url": "https://github.com/canonical/nginx/pull/248",
                "number": 248,
                "state": "closed",
                "created_at": "2026-06-01T00:00:00Z",
                "closed_at": "2026-07-01T00:00:00Z",
                "repository_url": "https://api.github.com/repos/canonical/nginx",
                "pull_request": {"merged_at": "2026-07-01T00:00:00Z"},
                "user": {"login": "someoneelse"},
            },
            {
                "title": "my own pr",
                "html_url": "https://github.com/canonical/nginx/pull/250",
                "number": 250,
                "state": "open",
                "created_at": "2026-06-05T00:00:00Z",
                "closed_at": None,
                "repository_url": "https://api.github.com/repos/canonical/nginx",
                "pull_request": {"merged_at": None},
                "user": {"login": "octocat"},
            },
        ]},
        status=200,
    )
    items = GithubReviewsFetcher().fetch(_config())
    assert len(items) == 1
    assert items[0].role == "reviewer"
    assert items[0].identifier == "#248"
    assert items[0].source == "github_review"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_reviews.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/github_reviews.py`:
```python
from __future__ import annotations

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


class GithubReviewsFetcher(Fetcher):
    name = "github_reviews"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        query = f"reviewed-by:{user} type:pr updated:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            query += f" {orgs}"
        out: list[WorkItem] = []
        for item in gh.search_issues(query):
            author = (item.get("user") or {}).get("login")
            if author == user:
                continue
            org, repo = gh.parse_repo(item["repository_url"])
            out.append(WorkItem(
                source="github_review",
                project=repo,
                org=org,
                title=item["title"],
                url=item["html_url"],
                date=gh.pick_issue_date(item),
                role="reviewer",
                state=gh.issue_state(item),
                identifier=f"#{item['number']}",
                extra={"author": author},
            ))
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_reviews.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/github_reviews.py tests/test_github_reviews.py
git commit -m "feat: add GitHub PRs-reviewed fetcher"
```

---

### Task 8: GitHub issues fetcher

**Files:**
- Create: `bragdoc/fetchers/github_issues.py`
- Test: `tests/test_github_issues.py`

- [ ] **Step 1: Write the failing test**

`tests/test_github_issues.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_issues import GithubIssuesFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_issues": True},
    )


@responses.activate
def test_fetch_normalizes_issue(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": [{
            "title": "redirect loop bug",
            "html_url": "https://github.com/canonical/nginx/issues/210",
            "number": 210,
            "state": "closed",
            "created_at": "2026-04-01T00:00:00Z",
            "closed_at": "2026-04-20T00:00:00Z",
            "repository_url": "https://api.github.com/repos/canonical/nginx",
        }]},
        status=200,
    )
    items = GithubIssuesFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_issue"
    assert it.role == "author"
    assert it.state == "closed"
    assert it.identifier == "#210"
    assert it.date == datetime(2026, 4, 20, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_issues.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/github_issues.py`:
```python
from __future__ import annotations

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


class GithubIssuesFetcher(Fetcher):
    name = "github_issues"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        query = f"author:{user} type:issue updated:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            query += f" {orgs}"
        out: list[WorkItem] = []
        for item in gh.search_issues(query):
            org, repo = gh.parse_repo(item["repository_url"])
            out.append(WorkItem(
                source="github_issue",
                project=repo,
                org=org,
                title=item["title"],
                url=item["html_url"],
                date=gh.pick_issue_date(item),
                role="author",
                state=gh.issue_state(item),
                identifier=f"#{item['number']}",
                extra={},
            ))
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_issues.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/github_issues.py tests/test_github_issues.py
git commit -m "feat: add GitHub issues fetcher"
```

---

### Task 9: GitHub commits fetcher

**Files:**
- Create: `bragdoc/fetchers/github_commits.py`
- Test: `tests/test_github_commits.py`

- [ ] **Step 1: Write the failing test**

`tests/test_github_commits.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_commits import GithubCommitsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_commits": True},
    )


@responses.activate
def test_fetch_normalizes_commit(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://api.github.com/search/commits",
        json={"items": [{
            "sha": "abcdef1234567890",
            "html_url": "https://github.com/canonical/aproxy-operator/commit/abcdef1234567890",
            "commit": {
                "message": "Fix proxy bug\n\nlong body",
                "author": {"date": "2026-05-14T09:00:00Z"},
            },
            "repository": {"name": "aproxy-operator", "owner": {"login": "canonical"}},
        }]},
        status=200,
    )
    items = GithubCommitsFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_commit"
    assert it.title == "Fix proxy bug"
    assert it.identifier == "abcdef1"
    assert it.project == "aproxy-operator"
    assert it.state is None
    assert it.date == datetime(2026, 5, 14, 9, 0, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_commits.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/github_commits.py`:
```python
from __future__ import annotations

import requests

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _search_commits(query: str, token: str | None = None) -> list[dict]:
    items: list[dict] = []
    page = 1
    headers = {
        "Authorization": f"Bearer {token or gh.github_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    while True:
        resp = requests.get(
            f"{gh.API}/search/commits",
            headers=headers,
            params={"q": query, "per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json().get("items", [])
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


class GithubCommitsFetcher(Fetcher):
    name = "github_commits"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        query = f"author:{user} author-date:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            query += f" {orgs}"
        out: list[WorkItem] = []
        for item in _search_commits(query):
            repo_info = item.get("repository", {})
            repo = repo_info.get("name", "")
            org = (repo_info.get("owner") or {}).get("login")
            message = item["commit"]["message"].splitlines()[0]
            out.append(WorkItem(
                source="github_commit",
                project=repo,
                org=org,
                title=message,
                url=item["html_url"],
                date=gh.parse_ts(item["commit"]["author"]["date"]),
                role="author",
                state=None,
                identifier=item["sha"][:7],
                extra={},
            ))
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_commits.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/github_commits.py tests/test_github_commits.py
git commit -m "feat: add GitHub commits fetcher"
```

---

### Task 10: GitHub discussions fetcher (GraphQL)

**Files:**
- Create: `bragdoc/fetchers/github_discussions.py`
- Test: `tests/test_github_discussions.py`

- [ ] **Step 1: Write the failing test**

`tests/test_github_discussions.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.github_discussions import GithubDiscussionsFetcher


def _config():
    return Config(
        identity={"github_username": "octocat"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=["canonical"],
        main_projects=[],
        sources={"github_discussions": True},
    )


@responses.activate
def test_fetch_normalizes_discussion(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    responses.add(
        responses.POST,
        "https://api.github.com/graphql",
        json={"data": {"search": {"nodes": [{
            "title": "How to configure aproxy",
            "url": "https://github.com/canonical/aproxy-operator/discussions/5",
            "number": 5,
            "createdAt": "2026-03-15T00:00:00Z",
            "repository": {"name": "aproxy-operator", "owner": {"login": "canonical"}},
        }]}}},
        status=200,
    )
    items = GithubDiscussionsFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "github_discussion"
    assert it.project == "aproxy-operator"
    assert it.identifier == "#5"
    assert it.role == "author"
    assert it.date == datetime(2026, 3, 15, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_github_discussions.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/github_discussions.py`:
```python
from __future__ import annotations

import requests

from bragdoc.config import Config
from bragdoc.fetchers import _github_common as gh
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem

_QUERY = """
query($q: String!) {
  search(query: $q, type: DISCUSSION, first: 100) {
    nodes {
      ... on Discussion {
        title
        url
        number
        createdAt
        repository { name owner { login } }
      }
    }
  }
}
"""


class GithubDiscussionsFetcher(Fetcher):
    name = "github_discussions"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and gh.github_token() is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        user = config.identity["github_username"]
        start = config.window_start.date().isoformat()
        q = f"author:{user} created:>={start}"
        orgs = gh.org_qualifier(config.github_orgs)
        if orgs:
            q += f" {orgs}"
        headers = {
            "Authorization": f"Bearer {gh.github_token()}",
            "Accept": "application/vnd.github+json",
        }
        resp = requests.post(
            f"{gh.API}/graphql",
            headers=headers,
            json={"query": _QUERY, "variables": {"q": q}},
            timeout=30,
        )
        resp.raise_for_status()
        nodes = resp.json()["data"]["search"]["nodes"]
        out: list[WorkItem] = []
        for node in nodes:
            if not node:
                continue
            repo_info = node.get("repository", {})
            out.append(WorkItem(
                source="github_discussion",
                project=repo_info.get("name", ""),
                org=(repo_info.get("owner") or {}).get("login"),
                title=node["title"],
                url=node["url"],
                date=gh.parse_ts(node["createdAt"]),
                role="author",
                state=None,
                identifier=f"#{node['number']}",
                extra={},
            ))
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_github_discussions.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/github_discussions.py tests/test_github_discussions.py
git commit -m "feat: add GitHub discussions fetcher"
```

---

### Task 11: Jira fetcher

**Files:**
- Create: `bragdoc/fetchers/jira.py`
- Test: `tests/test_jira.py`

- [ ] **Step 1: Write the failing test**

`tests/test_jira.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.jira import JiraFetcher


def _config():
    return Config(
        identity={"jira_email": "me@example.com", "jira_server": "https://ex.atlassian.net"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=[],
        main_projects=[],
        sources={"jira": True},
    )


def test_enabled_requires_token(monkeypatch):
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    assert JiraFetcher().enabled(_config()) is False
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    assert JiraFetcher().enabled(_config()) is True


@responses.activate
def test_fetch_normalizes_issue(monkeypatch):
    monkeypatch.setenv("JIRA_API_TOKEN", "t")
    responses.add(
        responses.GET,
        "https://ex.atlassian.net/rest/api/3/search",
        json={"issues": [{
            "key": "PS-456",
            "fields": {
                "summary": "Aproxy subordinate charm spec",
                "status": {"name": "Done"},
                "updated": "2026-04-10T12:00:00.000+0000",
                "project": {"key": "PS"},
            },
        }], "total": 1, "startAt": 0, "maxResults": 50},
        status=200,
    )
    items = JiraFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "jira"
    assert it.project == "PS"
    assert it.identifier == "PS-456"
    assert it.state == "Done"
    assert it.url == "https://ex.atlassian.net/browse/PS-456"
    assert it.date == datetime(2026, 4, 10, 12, 0, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_jira.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/jira.py`:
```python
from __future__ import annotations

import os
from datetime import datetime

import requests

from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _parse_jira_ts(value: str) -> datetime:
    # Jira format: 2026-04-10T12:00:00.000+0000 -> add colon in tz offset
    if value[-5] in "+-" and value[-3] != ":":
        value = value[:-2] + ":" + value[-2:]
    return datetime.fromisoformat(value)


class JiraFetcher(Fetcher):
    name = "jira"

    def enabled(self, config: Config) -> bool:
        return config.source_enabled(self.name) and os.environ.get("JIRA_API_TOKEN") is not None

    def fetch(self, config: Config) -> list[WorkItem]:
        server = config.identity["jira_server"].rstrip("/")
        email = config.identity["jira_email"]
        token = os.environ["JIRA_API_TOKEN"]
        start = config.window_start.date().isoformat()
        jql = f'assignee = currentUser() AND updated >= "{start}" ORDER BY updated DESC'
        out: list[WorkItem] = []
        start_at = 0
        while True:
            resp = requests.get(
                f"{server}/rest/api/3/search",
                params={"jql": jql, "startAt": start_at, "maxResults": 50,
                        "fields": "summary,status,updated,project"},
                auth=(email, token),
                headers={"Accept": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for issue in data.get("issues", []):
                fields = issue["fields"]
                out.append(WorkItem(
                    source="jira",
                    project=fields["project"]["key"],
                    org=None,
                    title=fields["summary"],
                    url=f"{server}/browse/{issue['key']}",
                    date=_parse_jira_ts(fields["updated"]),
                    role="author",
                    state=fields["status"]["name"],
                    identifier=issue["key"],
                    extra={},
                ))
            start_at += len(data.get("issues", []))
            if start_at >= data.get("total", 0) or not data.get("issues"):
                break
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_jira.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/jira.py tests/test_jira.py
git commit -m "feat: add Jira fetcher"
```

---

### Task 12: Discourse fetcher

**Files:**
- Create: `bragdoc/fetchers/discourse.py`
- Test: `tests/test_discourse.py`

- [ ] **Step 1: Write the failing test**

`tests/test_discourse.py`:
```python
from datetime import datetime, timezone
import responses
from bragdoc.config import Config
from bragdoc.fetchers.discourse import DiscourseFetcher


def _config():
    return Config(
        identity={"discourse_base_url": "https://d.example.com", "discourse_username": "octo"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=[],
        main_projects=[],
        sources={"discourse": True},
    )


@responses.activate
def test_fetch_normalizes_actions(monkeypatch):
    monkeypatch.setenv("DISCOURSE_API_KEY", "k")
    responses.add(
        responses.GET,
        "https://d.example.com/user_actions.json",
        json={"user_actions": [{
            "title": "Announcing the aproxy charm",
            "created_at": "2026-05-01T00:00:00.000Z",
            "slug": "announcing-the-aproxy-charm",
            "topic_id": 42,
            "post_number": 1,
            "category_id": 7,
        }]},
        status=200,
    )
    items = DiscourseFetcher().fetch(_config())
    assert len(items) == 1
    it = items[0]
    assert it.source == "discourse"
    assert it.title == "Announcing the aproxy charm"
    assert it.url == "https://d.example.com/t/announcing-the-aproxy-charm/42/1"
    assert it.date == datetime(2026, 5, 1, tzinfo=timezone.utc)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_discourse.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/discourse.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_discourse.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/discourse.py tests/test_discourse.py
git commit -m "feat: add Discourse fetcher"
```

---

### Task 13: Launchpad fetcher

**Files:**
- Create: `bragdoc/fetchers/launchpad.py`
- Test: `tests/test_launchpad.py`

Launchpad uses `launchpadlib` (hard to mock over HTTP), so normalization is factored into pure functions that take plain dicts. The test covers those; `fetch()` wires them to `launchpadlib` at runtime.

- [ ] **Step 1: Write the failing test**

`tests/test_launchpad.py`:
```python
from datetime import datetime, timezone
from bragdoc.config import Config
from bragdoc.fetchers.launchpad import (
    LaunchpadFetcher, normalize_bug_task, normalize_merge_proposal,
)


def _config(enabled=True):
    return Config(
        identity={"launchpad_user": "octo"},
        window_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
        github_orgs=[],
        main_projects=[],
        sources={"launchpad": enabled},
    )


def test_enabled_toggle():
    assert LaunchpadFetcher().enabled(_config(enabled=False)) is False


def test_normalize_bug_task():
    raw = {
        "title": "Bug #1: crash on start",
        "web_link": "https://bugs.launchpad.net/foo/+bug/1",
        "status": "Fix Released",
        "date_created": "2026-03-01T00:00:00+00:00",
        "bug_target_name": "foo",
        "bug_id": 1,
    }
    it = normalize_bug_task(raw)
    assert it.source == "launchpad"
    assert it.project == "foo"
    assert it.identifier == "LP#1"
    assert it.state == "Fix Released"
    assert it.date == datetime(2026, 3, 1, tzinfo=timezone.utc)


def test_normalize_merge_proposal():
    raw = {
        "web_link": "https://code.launchpad.net/~octo/foo/+merge/42",
        "queue_status": "Merged",
        "date_created": "2026-04-01T00:00:00+00:00",
        "target_branch_name": "foo",
        "mp_id": 42,
        "description": "Add feature X",
    }
    it = normalize_merge_proposal(raw)
    assert it.source == "launchpad"
    assert it.project == "foo"
    assert it.identifier == "MP!42"
    assert it.state == "Merged"
    assert it.title == "Add feature X"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_launchpad.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/launchpad.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_launchpad.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/launchpad.py tests/test_launchpad.py
git commit -m "feat: add Launchpad fetcher with pure normalizers"
```

---

### Task 14: Fetcher registry

**Files:**
- Create: `bragdoc/fetchers/registry.py`
- Test: `tests/test_registry.py`

- [ ] **Step 1: Write the failing test**

`tests/test_registry.py`:
```python
from bragdoc.fetchers.registry import all_fetchers


def test_registry_lists_all_eight_sources():
    names = {f.name for f in all_fetchers()}
    assert names == {
        "github_prs", "github_reviews", "github_issues", "github_commits",
        "github_discussions", "jira", "discourse", "launchpad",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/fetchers/registry.py`:
```python
from __future__ import annotations

from bragdoc.fetchers.base import Fetcher
from bragdoc.fetchers.discourse import DiscourseFetcher
from bragdoc.fetchers.github_commits import GithubCommitsFetcher
from bragdoc.fetchers.github_discussions import GithubDiscussionsFetcher
from bragdoc.fetchers.github_issues import GithubIssuesFetcher
from bragdoc.fetchers.github_prs import GithubPrsFetcher
from bragdoc.fetchers.github_reviews import GithubReviewsFetcher
from bragdoc.fetchers.jira import JiraFetcher
from bragdoc.fetchers.launchpad import LaunchpadFetcher


def all_fetchers() -> list[Fetcher]:
    return [
        GithubPrsFetcher(),
        GithubReviewsFetcher(),
        GithubIssuesFetcher(),
        GithubCommitsFetcher(),
        GithubDiscussionsFetcher(),
        JiraFetcher(),
        DiscourseFetcher(),
        LaunchpadFetcher(),
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_registry.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/fetchers/registry.py tests/test_registry.py
git commit -m "feat: add fetcher registry"
```

---

### Task 15: Aggregator

**Files:**
- Create: `bragdoc/aggregator.py`
- Test: `tests/test_aggregator.py`

- [ ] **Step 1: Write the failing test**

`tests/test_aggregator.py`:
```python
from datetime import datetime, timezone
from bragdoc.aggregator import collect, write_cache, read_cache
from bragdoc.config import Config
from bragdoc.fetchers.base import Fetcher
from bragdoc.models import WorkItem


def _config():
    return Config(
        identity={}, window_start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        window_end=datetime(2026, 9, 1, tzinfo=timezone.utc),
        github_orgs=[], main_projects=[], sources={},
    )


def _item(date):
    return WorkItem("github_pr", "repo", "canonical", "t", "u", date,
                    "author", "merged", "#1", {})


class GoodFetcher(Fetcher):
    name = "good"

    def enabled(self, config):
        return True

    def fetch(self, config):
        return [
            _item(datetime(2026, 5, 1, tzinfo=timezone.utc)),   # in window
            _item(datetime(2026, 1, 1, tzinfo=timezone.utc)),   # before window
        ]


class DisabledFetcher(Fetcher):
    name = "disabled"

    def enabled(self, config):
        return False

    def fetch(self, config):
        raise AssertionError("must not be called")


class BrokenFetcher(Fetcher):
    name = "broken"

    def enabled(self, config):
        return True

    def fetch(self, config):
        raise RuntimeError("boom")


def test_collect_filters_window_and_skips_disabled_and_broken():
    items = collect(_config(), [GoodFetcher(), DisabledFetcher(), BrokenFetcher()])
    assert len(items) == 1
    assert items[0].date == datetime(2026, 5, 1, tzinfo=timezone.utc)


def test_cache_roundtrip(tmp_path):
    path = tmp_path / "cache.json"
    items = [_item(datetime(2026, 5, 1, tzinfo=timezone.utc))]
    write_cache(items, str(path))
    restored = read_cache(str(path))
    assert restored == items
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_aggregator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/aggregator.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_aggregator.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/aggregator.py tests/test_aggregator.py
git commit -m "feat: add aggregator with window filter and JSON cache"
```

---

### Task 16: Renderer

**Files:**
- Create: `bragdoc/renderer.py`
- Test: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing test**

`tests/test_renderer.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_renderer.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/renderer.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_renderer.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add bragdoc/renderer.py tests/test_renderer.py
git commit -m "feat: add markdown renderer with project/collaboration grouping"
```

---

### Task 17: CLI

**Files:**
- Create: `bragdoc/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

`tests/test_cli.py`:
```python
from datetime import datetime, timezone
from bragdoc.cli import main
from bragdoc.models import WorkItem
from bragdoc.aggregator import write_cache


def _item():
    return WorkItem("github_pr", "aproxy-operator", "canonical", "PS7",
                    "https://x/1", datetime(2026, 5, 1, tzinfo=timezone.utc),
                    "author", "merged", "#1", {})


def _config_files(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "identity:\n"
        "  github_username: octo\n"
        "date_range:\n"
        "  start: \"2026-03-01\"\n"
        "  end: \"2026-09-01\"\n"
        "scope:\n"
        "  github_orgs: []\n"
        "  main_projects: [aproxy-operator]\n"
        "sources: {}\n"
    )
    env = tmp_path / ".env"
    env.write_text("")
    return cfg, env


def test_render_command_reads_cache_and_writes_output(tmp_path):
    cfg, env = _config_files(tmp_path)
    cache = tmp_path / "cache.json"
    write_cache([_item()], str(cache))
    out = tmp_path / "digest.md"
    rc = main([
        "render",
        "--config", str(cfg),
        "--env", str(env),
        "--cache", str(cache),
        "--output", str(out),
    ])
    assert rc == 0
    text = out.read_text()
    assert "# Brag Digest — octo" in text
    assert "aproxy-operator" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

`bragdoc/cli.py`:
```python
from __future__ import annotations

import argparse
import os
from datetime import datetime

from bragdoc.aggregator import collect, read_cache, write_cache
from bragdoc.config import load_config
from bragdoc.fetchers.registry import all_fetchers
from bragdoc.renderer import render_markdown


def _default_output() -> str:
    return f"output/brag-digest-{datetime.now().date().isoformat()}.md"


def _do_fetch(config, cache_path: str) -> None:
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    items = collect(config, all_fetchers())
    write_cache(items, cache_path)
    print(f"[bragdoc] wrote {len(items)} items to {cache_path}")


def _do_render(config, cache_path: str, output_path: str) -> None:
    items = read_cache(cache_path)
    md = render_markdown(
        items,
        main_projects=config.main_projects,
        username=config.identity.get("github_username", "me"),
        window=(config.window_start, config.window_end),
    )
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"[bragdoc] wrote digest to {output_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bragdoc")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--cache", default="cache/workitems.json")
    parser.add_argument("--output", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch")
    sub.add_parser("render")
    sub.add_parser("run")
    args = parser.parse_args(argv)

    config = load_config(args.config, args.env)
    output = args.output or _default_output()

    if args.command == "fetch":
        _do_fetch(config, args.cache)
    elif args.command == "render":
        _do_render(config, args.cache, output)
    elif args.command == "run":
        _do_fetch(config, args.cache)
        _do_render(config, args.cache, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -v`
Expected: PASS (all tests green)

- [ ] **Step 6: Commit**

```bash
git add bragdoc/cli.py tests/test_cli.py
git commit -m "feat: add CLI with fetch/render/run commands"
```

---

### Task 18: README + example run

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

`README.md`:
```markdown
# bragdoc

Generate an organized "brag digest" of your work across GitHub, Jira, Discourse,
and Launchpad over a configurable window (default: last 6 months). Output is a
Markdown file grouped by project + a cross-team/collaboration section — raw
material for writing your 360 brag document.

## Install

```bash
pip install -e '.[dev,launchpad]'
```

## Configure

```bash
cp config.example.yaml config.yaml   # edit identity, orgs, main_projects
cp .env.example .env                 # add your tokens
```

Required token scopes:
- `GITHUB_TOKEN`: classic PAT with `repo` + `read:org` (and `read:discussion`).
- `JIRA_API_TOKEN`: Atlassian API token paired with `jira_email`.
- `DISCOURSE_API_KEY` (optional): user API key.
- `LAUNCHPAD_CREDENTIALS` (optional): path to a launchpadlib credentials file.

Any source with a missing token is skipped with a warning — it never crashes.

## Use

```bash
bragdoc fetch     # hit the APIs, write cache/workitems.json
bragdoc render    # read cache, write output/brag-digest-YYYY-MM-DD.md
bragdoc run       # fetch then render
```

Re-run `render` freely to tweak formatting without re-fetching.

## Test

```bash
python -m pytest -v
```
```

- [ ] **Step 2: Verify the CLI is wired**

Run: `bragdoc --help`
Expected: usage text listing `fetch`, `render`, `run`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage"
```

---

## Self-Review Notes

- **Spec coverage:** All 8 sources (Tasks 6–13) → `WorkItem` (Task 2); config + secrets model (Task 3); fetch→cache→render two-phase flow (Tasks 15–17); by-repo + collaboration grouping (Task 16); optional/skip-on-missing-token behavior (fetcher `enabled()` + aggregator try/except); testing strategy (per-fetcher normalization + renderer grouping + config). Output sample matches renderer format.
- **Method/type consistency:** `WorkItem` fields and `Config.source_enabled` / `window_start` / `window_end` / `github_orgs` / `main_projects` are used identically across all tasks. Shared GitHub helpers (`search_issues`, `parse_repo`, `pick_issue_date`, `issue_state`, `parse_ts`, `org_qualifier`) defined in Task 5 and reused in Tasks 6–10.
- **Deviations from spec:** added `_github_common.py` (DRY helper) and `registry.py` (single source list) under `fetchers/` — internal, consistent with the modular design.
```
