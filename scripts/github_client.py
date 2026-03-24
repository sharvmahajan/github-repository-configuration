# scripts/github_client.py
"""
Centralized GitHub API client factory.
Handles authentication and provides the authenticated Github instance.
All other modules should import get_github_client() instead of creating Github() directly.
"""

import os
from github import Github, GithubException
import logging

logger = logging.getLogger(__name__)

_github_client = None
try:
    from dotenv import load_dotenv
    load_dotenv()  # Loads variables from .env into os.environ
    logging.getLogger(__name__).debug("Loaded .env file for local development")
except ImportError:
    logging.getLogger(__name__).debug("python-dotenv not installed - skipping .env load")

def get_github_client() -> Github:
    """
    Returns a singleton authenticated Github client.
    Uses GITHUB_TOKEN from environment (preferred in Actions).
    Falls back to ENFORCER_TOKEN if set (for local testing or special cases).
    """
    global _github_client
    if _github_client is not None:
        return _github_client

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ENFORCER_TOKEN")

    if not token:
        raise ValueError(
            "No GitHub authentication token found. "
            "Set GITHUB_TOKEN (Actions) or ENFORCER_TOKEN (local)."
        )

    try:
        _github_client = Github(token)
        user = _github_client.get_user()
        logger.info(f"Authenticated as: {user.login}")
    except GithubException as e:
        raise RuntimeError(f"GitHub authentication failed: {e}") from e

    return _github_client