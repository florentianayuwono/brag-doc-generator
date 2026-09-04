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
