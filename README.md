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
                  #   (also writes output/brag-digest-YYYY-MM-DD-prompt.md)
bragdoc run       # fetch then render
bragdoc prompt    # (re)write just the LLM prompt file, no fetch/cache needed
```

Re-run `render` freely to tweak formatting without re-fetching.

## Turning the digest into a brag document with your own LLM

`render` (and `run`) also writes a companion `*-prompt.md` file — a ready-to-use
prompt instructing an AI assistant to turn the raw digest into a polished,
**1-2 page** brag document following Julia Evans' template
(https://jvns.ca/blog/brag-documents/): Goals for this/next year, Projects,
Collaboration & mentorship, Design & documentation, Company building, What
you learned, and Outside of work.

To use it:
1. Optionally fill in `goals.this_year` / `goals.next_year` in `config.yaml`.
2. Open the `*-prompt.md` file and the `*.md` digest.
3. Paste both into your LLM of choice (ChatGPT, Claude, Copilot Chat, etc.) —
   the prompt tells it to only use facts from the digest and to ask you
   before inventing any impact/metrics it can't find there.

## Test

```bash
python -m pytest -v
```
