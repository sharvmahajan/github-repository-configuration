# scripts/get_repos.py
"""
Functions to retrieve GitHub repositories based on different filters.
Uses the centralized GitHub client and global config.
Supports both organization and personal account modes.
"""

from typing import List, Optional
from github import Github, Repository, GithubException, Organization, NamedUser
import logging

from .github_client import get_github_client
from .config_loader import load_global_config

logger = logging.getLogger(__name__)


def get_repos(
    team_slug: Optional[str] = None,
    single_repo_name: Optional[str] = None,
    skip_archived: bool = True,
    skip_forks: bool = True,
) -> List[Repository.Repository]:
    """
    Retrieve repositories to process based on criteria.

    Modes:
      - single_repo_name: return only that repo (personal or org)
      - team_slug: repos accessible by that team (organization only)
      - default: all repos in organization or personal account

    Args:
        team_slug: Team slug (org mode only)
        single_repo_name: Specific repo name (e.g. "mcd-framework-test")
        skip_archived: Exclude archived repos (default True)
        skip_forks: Exclude forked repos (default True)

    Returns:
        List of github.Repository.Repository objects

    Raises:
        ValueError: If required config missing
        GithubException: On API errors
    """
    g = get_github_client()
    config = load_global_config()

    org_name = config.get("organization")
    repos: List[Repository.Repository] = []

    # Determine target (org or personal user)
    target = None
    is_org = False

    if org_name:
        try:
            target = g.get_organization(org_name)
            is_org = True
            logger.info(f"Using organization mode: {org_name}")
        except GithubException as e:
            if e.status == 404:
                logger.warning(f"Organization '{org_name}' not found (404) → falling back to personal user mode")
            else:
                raise

    if target is None:
        # Personal user fallback
        target = g.get_user()
        logger.info(f"Using personal account mode: {target.login}")

    # 1. Single repo mode
    if single_repo_name:
        try:
            if is_org:
                repo = target.get_repo(single_repo_name)  # Organization.get_repo
            else:
                repo = target.get_repo(single_repo_name)  # AuthenticatedUser.get_repo
            if (not skip_archived or not repo.archived) and (not skip_forks or not repo.fork):
                repos.append(repo)
                logger.info(f"Selected single repo: {repo.full_name}")
            else:
                logger.warning(f"Skipped single repo {single_repo_name} (archived or fork)")
        except GithubException as e:
            logger.error(f"Repo '{single_repo_name}' not found or inaccessible: {e}")
        return repos

    # 2. Team-specific mode (org only)
    if team_slug and is_org:
        try:
            team = target.get_team_by_slug(team_slug)  # type: Organization.Team
            logger.info(f"Fetching repos for team: {team_slug}")
            for repo in team.get_repos():
                if (not skip_archived or not repo.archived) and (not skip_forks or not repo.fork):
                    repos.append(repo)
        except GithubException as e:
            logger.error(f"Team '{team_slug}' not found or error: {e}")
        return repos

    # 3. All repos mode
    logger.info(f"Fetching all matching repositories from {target.login if not is_org else org_name}")
    repo_iterator = target.get_repos() if hasattr(target, 'get_repos') else []

    for repo in repo_iterator:
        if (not skip_archived or not repo.archived) and (not skip_forks or not repo.fork):
            repos.append(repo)

    logger.info(f"Found {len(repos)} repositories to process")
    return repos