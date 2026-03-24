# scripts/branch_protection.py
"""
Enforces branch protection rules on the default branch.
Loads configuration from global.yaml.
Supports dry-run mode.
"""

from typing import List, Dict, Any
from github import Repository, GithubException, Branch
import logging

from .github_client import get_github_client
from .config_loader import load_global_config

logger = logging.getLogger(__name__)


def enforce_branch_protection(
    repo: Repository.Repository,
    dry_run: bool = True,
) -> List[str]:
    """
    Apply branch protection rules to the default branch based on global.yaml.
    
    Returns list of messages describing actions taken or would be taken.
    """
    changes = []

    config = load_global_config()
    bp_config = config.get("branch_protection", {})
    
    if not bp_config.get("enabled", False):
        changes.append(f"Branch protection is disabled in config for {repo.full_name}")
        return changes

    branch_name = bp_config.get("branch", repo.default_branch)
    if not branch_name:
        changes.append(f"No branch name specified and no default branch in {repo.full_name} - skipping")
        return changes

    try:
        branch: Branch.Branch = repo.get_branch(branch_name)
    except GithubException as e:
        if e.status == 404:
            changes.append(f"Branch '{branch_name}' does not exist in {repo.full_name} - skipping protection")
            return changes
        else:
            changes.append(f"Error accessing branch '{branch_name}' in {repo.full_name}: {e}")
            return changes

    # Desired protection settings from config
    desired = {
        "required_approving_review_count": bp_config.get("required_approving_review_count", 1),
        "require_code_owner_reviews": bp_config.get("require_code_owner_reviews", True),
        "dismiss_stale_reviews": bp_config.get("dismiss_stale_reviews", True),
        "strict": bp_config.get("required_status_checks", {}).get("strict", True),
        "contexts": bp_config.get("required_status_checks", {}).get("contexts", []),
        "enforce_admins": bp_config.get("enforce_admins", True),
        "allow_force_pushes": bp_config.get("allow_force_pushes", False),
        "allow_deletions": bp_config.get("allow_deletions", False),
    }

    # Only add push restrictions if the repo is in an organization
    if repo.organization:
        desired.update({
            "user_push_restrictions": bp_config.get("restrictions", {}).get("users", []),
            "team_push_restrictions": bp_config.get("restrictions", {}).get("teams", []),
            "app_push_restrictions": bp_config.get("restrictions", {}).get("apps", []),
        })
    else:
        changes.append(f"Skipping push restrictions on personal repo {repo.full_name} (not supported by GitHub)")

    # Apply protection
    if dry_run:
        changes.append(f"[DRY-RUN] Would protect branch '{branch_name}' in {repo.full_name}")
        changes.append("  Settings that would be applied:")
        for key, value in desired.items():
            if value or value == []:  # show even if empty list
                changes.append(f"    {key}: {value}")
    else:
        try:
            branch.edit_protection(**desired)
            changes.append(f"Successfully protected branch '{branch_name}' in {repo.full_name}")
        except GithubException as e:
            changes.append(f"Failed to protect '{branch_name}' in {repo.full_name}: {e}")

    return changes