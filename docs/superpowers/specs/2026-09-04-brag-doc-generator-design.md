# Brag Doc Generator — Design

Date: 2026-09-04
Author: Florentiana Yuwono
Status: Approved (pending spec review)

## Purpose

Automate the data-gathering step of writing a 360 brag document. The tool
fetches the author's work from GitHub, Jira, Discourse, and Launchpad over a
configurable window (default: last 6 months) and produces an **organized raw
digest** in Markdown. The author writes the narrative ("Contributions",
"Impacts") themselves — the tool does not generate prose.

This mirrors the existing brag-doc template, which is structured by **Project**
with a separate **Collaboration & mentorship** section.

## Scope

### In scope
- Fetch and normalize work items from 8 sources (all optional):
  - GitHub: PRs authored, PRs reviewed, issues opened/closed, commits authored, discussions
  - Jira: issues assigned to / worked by the user
  - Discourse: topics/posts authored
  - Launchpad: bugs / merge proposals
- Group items by repo/project, with a dedicated Cross-team & collaboration bucket.
- Emit a Markdown digest with links, dates, identifiers, and states.
- Cache normalized data as JSON so rendering can be re-run without re-fetching.

### Out of scope
- LLM-generated narrative or "impact" statements.
- Editing/committing the final brag document itself.
- Non-API sources behind manual login walls (Google Docs specs, internal wikis).

## Chosen approach

**Modular package with per-source fetchers + normalized data model + renderer,
combined with a two-phase fetch→cache→render flow.**

Each source is an isolated fetcher module returning a common `WorkItem`. An
aggregator runs the enabled fetchers and writes a JSON cache. A renderer reads
the cache and emits Markdown. Fetching (network-bound, slow) and rendering
(instant, re-runnable) are separate commands, so formatting/grouping can be
tweaked without re-hitting APIs.

Alternatives considered:
- **Monolithic script** — fastest to write, but tangled and hard to test/extend across 8 sources. Rejected.
- **Pure two-phase without modular fetchers** — good iteration, but without isolated fetchers the fetch step becomes the same monolith problem. Folded the caching idea into the modular approach instead.

## Project layout

```
brag-doc-generator/
├── bragdoc/
│   ├── __init__.py
│   ├── models.py                 # WorkItem dataclass (the normalized unit)
│   ├── config.py                 # loads config.yaml + .env, validates
│   ├── cli.py                    # entrypoint: fetch / render / run
│   ├── aggregator.py             # runs enabled fetchers, collects WorkItems, writes cache JSON
│   ├── renderer.py               # reads WorkItems, groups, emits markdown
│   └── fetchers/
│       ├── base.py               # Fetcher ABC/protocol: name, enabled(config), fetch() -> list[WorkItem]
│       ├── github_prs.py         # PRs authored
│       ├── github_reviews.py     # PRs reviewed
│       ├── github_issues.py      # issues opened/closed
│       ├── github_commits.py     # commits authored
│       ├── github_discussions.py # discussions (GraphQL)
│       ├── jira.py
│       ├── discourse.py
│       └── launchpad.py
├── tests/                        # one test file per fetcher + renderer + config, mocked HTTP
├── config.example.yaml
├── .env.example
├── .gitignore                    # ignores .env, cache/, output/
├── pyproject.toml
└── README.md
```

Each fetcher is small and isolated, returns the same `WorkItem` type, and
declares itself enabled only if its token/config is present. Adding or removing
a source touches exactly one file.

## Data model

Every fetcher normalizes results into a single shape so the renderer needs no
source-specific logic:

```python
@dataclass
class WorkItem:
    source: str          # "github_pr" | "github_review" | "github_issue" |
                         # "github_commit" | "github_discussion" | "jira" |
                         # "discourse" | "launchpad"
    project: str         # repo name ("aproxy-operator"), Jira project key, or Discourse category
    org: str | None      # "canonical", or None for Jira/Discourse
    title: str           # PR/issue/ticket title or commit summary
    url: str             # permalink
    date: datetime       # merged/closed date if available, else created date
    role: str            # "author" | "reviewer" — routes project vs collaboration bucket
    state: str | None    # "merged" | "open" | "closed" | "done" | ...
    identifier: str      # "#123" | "PROJ-456" | commit sha[:8]
    extra: dict          # source-specific extras (additions/deletions, labels, etc.)
```

Decisions:
- **`date`**: use merged date for merged PRs, closed date for closed issues,
  else created date — so the window reflects when work landed.
- **`role`**: `author` items group under their project; `reviewer` items (plus
  authored items in repos not listed in `main_projects`) flow to the
  Cross-team & collaboration section.

## Configuration & secrets

Secrets never committed. Non-secret settings live in a committed-safe YAML.

`.env` (gitignored — secrets only):
```
GITHUB_TOKEN=ghp_...
JIRA_API_TOKEN=...
DISCOURSE_API_KEY=...        # optional
LAUNCHPAD_CREDENTIALS=...    # optional (or launchpadlib OAuth cache file path)
```

`config.yaml` (committed-safe — non-secret settings):
```yaml
identity:
  github_username: florentianayuwono
  jira_email: florentiana.yuwono@canonical.com
  jira_server: https://warthogs.atlassian.net
  discourse_base_url: https://discourse.canonical.com
  discourse_username: florenyu
  launchpad_user: florenyu

date_range:
  months_back: 6            # or set explicit start/end to override

scope:
  github_orgs: [canonical]  # orgs to search authored/review/issue activity in
  main_projects:            # repos that are "yours" -> own Project section
    - github-actions-runner
    - github-runner-image-builder-operator
    - github-runner-operators
    - github-runner-operator
    - content-cache-operator
    - ingress-configurator-operator
  # anything else touched -> Cross-team & collaboration section

sources:                    # explicit on/off per source
  github_prs: true
  github_reviews: true
  github_issues: true
  github_commits: true
  github_discussions: true
  jira: true
  discourse: true
  launchpad: true
```

A source runs only if **both** its `sources:` toggle is true **and** its
required token/config is present. Missing token → skip with a printed warning,
never a crash. The real `config.yaml` will be pre-filled with the author's
username/repos as defaults, to be confirmed/corrected.

## Data flow & CLI

```
config.yaml + .env
      |
      v
  aggregator --> for each enabled fetcher: fetch() --> list[WorkItem]
      |
      v
  cache/workitems.json          (phase 1 output: raw normalized dump)
      |
      v
  renderer --> group + sort --> output/brag-digest-YYYY-MM-DD.md
```

Commands:
- `bragdoc fetch` — hits the APIs, writes `cache/workitems.json` (slow, network-bound).
- `bragdoc render` — reads the cache, writes the Markdown digest (instant, no network, re-runnable).
- `bragdoc run` — `fetch` then `render`.

Renderer grouping logic:
1. Split items into `author` vs `reviewer`.
2. `author` items whose `project` ∈ `main_projects` → grouped under that Project heading.
3. Everything else (`reviewer` items + `author` items in non-main repos) → Cross-team & collaboration, sub-grouped by repo.
4. Within each group, sort by `date` descending; render as Markdown bullets with title, identifier, state, date, link.
5. Jira tickets nest under a repo when a project key maps to it (config-driven), else render in their own Jira subsection.

## Output sample

```markdown
# Brag Digest — Florentiana Yuwono
Window: 2026-03-04 → 2026-09-04 · Generated 2026-09-04

## Summary
Authored: 42 PRs · 8 issues · 130 commits · Reviewed: 27 PRs · Jira: 15 done · Discourse: 3 · Launchpad: 2

## Projects
### aproxy-operator
- **Add PS7 PostgreSQL proxy support** — PR #123 · merged · 2026-05-14 · https://github.com/canonical/aproxy-operator/pull/123
- **ISD249 tutorial docs** — PR #131 · merged · 2026-06-02 · ...
  - _Jira:_ PROJ-456 Aproxy subordinate charm spec · done · 2026-04-10

### github-runner-operators
- ...

## Cross-team & collaboration
### nginx-ingress-integrator-operator (reviewer / cross-TZ)
- **Reviewed: fix ingress class bug** — PR #248 · merged · 2026-07-01 · ...
- **Fix redirect loop** — issue #210 · closed · ...

## Uncategorized / other repos
- ...
```

## Error handling

- Missing token/config for a source → warn and skip, keep going.
- API auth failure (bad token) → clear message naming the source; other sources still run.
- GitHub rate limits → respect `Retry-After` / back off; report partial results rather than dying.
- `fetch` writes the cache only after a source succeeds (per-source try/except), so one failing source never corrupts the file.

## Testing

- Unit-test each fetcher's normalization: raw API JSON fixture → expected `WorkItem`, with mocked HTTP (no live calls).
- Test renderer grouping logic with hand-built `WorkItem` lists (author vs reviewer, main vs non-main repo).
- Test config loader: missing token disables a source; toggles respected.

## Dependencies (anticipated)

- `PyGithub` or `requests` for GitHub REST; GraphQL (via `requests`) for discussions.
- `jira` (or `requests`) for Jira.
- `launchpadlib` for Launchpad (optional import — only when enabled).
- `requests` for Discourse.
- `PyYAML` for config, `python-dotenv` for `.env`.
- `pytest` + `responses`/`requests-mock` for tests.

Exact library choices (e.g. PyGithub vs raw REST) are finalized in the
implementation plan.
