from __future__ import annotations


def _goals_line(goals: str) -> str:
    return goals.strip() if goals.strip() else "(not provided — ask me for my goals before writing this section)"


def render_prompt(username: str, goals_this_year: str, goals_next_year: str,
                  digest_filename: str) -> str:
    """Build an LLM prompt that turns the raw digest into a brag document.

    Follows the template from Julia Evans' "brag documents" post:
    https://jvns.ca/blog/brag-documents/
    """
    this_year = _goals_line(goals_this_year)
    next_year = _goals_line(goals_next_year)

    return f"""\
# Brag document — writing instructions for the AI

You are helping **{username}** turn a raw work-activity digest into a polished
brag document, following the template from Julia Evans' post
"brag documents" (https://jvns.ca/blog/brag-documents/).

## Input

The raw digest is attached/pasted below (or in `{digest_filename}`). It lists
GitHub PRs, reviews, issues, commits, discussions, Jira tickets, Discourse
posts, and Launchpad activity from the last 6 months, already grouped by
project vs. cross-team collaboration.

## Hard constraints

- **Length: 1-2 pages total** (roughly 500-900 words). Be selective — group
  similar/minor items into one bullet rather than listing every PR
  individually. Prioritize the most impactful, highest-effort work.
- **Only use facts present in the digest.** Do not invent metrics, dates,
  outcomes, or impact numbers that aren't in the source data. If the digest
  doesn't state an impact/result, either omit it or phrase it plainly (e.g.
  "shipped X" instead of inventing "which reduced latency by 40%").
- If something is unclear or you'd need more context to describe the impact
  well, ask me a clarifying question instead of guessing.
- Write in first person, plain and confident tone — "exactly as good as it
  is", not exaggerated.

## Output format — use these sections, in this order

### Goals for this year
{this_year}

### Goals for next year
{next_year}

### Projects
For each major project: what my contributions were (design, implementation,
testing, docs, etc.) and the impact (who it's for, any numbers, what it
unblocked). Group related PRs/commits/tickets from the digest under one
project entry instead of listing each individually.

### Collaboration & mentorship
Code reviews, mentoring, cross-team bug fixes, pairing, answering questions
for other teams — pull these from "PRs reviewed" and any cross-team items in
the digest.

### Design & documentation
Design docs and documentation written or reviewed, with a one-line note on
why each doc mattered (e.g. "reduced repeat questions about X").

### Company building
Process improvements, interviewing/recruiting, culture/community work —
only include if present in the digest or if I mention it separately.

### What you learned
New skills, tools, or areas of the codebase I picked up — infer from the
variety/type of work in the digest (e.g. a new language, a new subsystem),
but ask me if you're not sure something counts as "learned" vs. just "used".

### Outside of work
Blog posts, talks, open source, industry recognition — only include if
mentioned in the digest or if I tell you about them separately.

## Now:

1. Read through the attached digest.
2. Draft the brag document above, keeping it to 1-2 pages.
3. Flag anywhere you had to guess or where more detail from me would help.
"""
