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
