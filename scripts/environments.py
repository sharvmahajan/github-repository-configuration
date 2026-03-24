# scripts/environments.py
"""
Enforces protected environments (qual, prod) in repositories.
Creates environments with protection rules from global.yaml.
Uses positional args for ReviewerParams (compatible with 2.5.0).
"""

from typing import List
from github import Repository, GithubException
from github.EnvironmentProtectionRuleReviewer import ReviewerParams
from github.EnvironmentDeploymentBranchPolicy import EnvironmentDeploymentBranchPolicyParams
import logging

from .config_loader import load_global_config

logger = logging.getLogger(__name__)


def enforce_environments(
    repo: Repository.Repository,
    dry_run: bool = True,
) -> List[str]:
    changes = []

    config = load_global_config()
    env_configs = config.get("environments", [])

    if not env_configs:
        msg = f"No 'environments' defined in global.yaml for {repo.full_name}"
        logger.warning(msg)
        changes.append(msg)
        return changes

    for env_cfg in env_configs:
        env_name = env_cfg.get("name")
        if not env_name:
            changes.append(f"Missing environment name in config for {repo.full_name}")
            continue

        wait_timer = env_cfg.get("wait_timer", 0)

        branch_policy_cfg = env_cfg.get("deployment_branch_policy", {})
        branch_policy = EnvironmentDeploymentBranchPolicyParams(
            protected_branches=branch_policy_cfg.get("protected_branches", True),
            custom_branch_policies=branch_policy_cfg.get("custom_branch_policies", False)
        )

        reviewers_cfg = env_cfg.get("required_reviewers", {})
        reviewers = []

        # Users – force int conversion
        for raw_id in reviewers_cfg.get("users", []):
            try:
                user_id = int(raw_id)
                reviewers.append(ReviewerParams("User", user_id))
            except (ValueError, TypeError):
                changes.append(
                    f"Invalid user ID '{raw_id}' (must be numeric integer) for '{env_name}'"
                )
                continue

        # Teams – force int conversion
        for raw_id in reviewers_cfg.get("teams", []):
            try:
                team_id = int(raw_id)
                reviewers.append(ReviewerParams("Team", team_id))
            except (ValueError, TypeError):
                changes.append(
                    f"Invalid team ID '{raw_id}' (must be numeric integer) for '{env_name}'"
                )
                continue

        if dry_run:
            changes.append(f"[DRY-RUN] Would create environment '{env_name}' in {repo.full_name}")
            changes.append(f"  Wait timer: {wait_timer} min")
            changes.append(
                f"  Branch policy: protected_branches={branch_policy.protected_branches}, "
                f"custom={branch_policy.custom_branch_policies}"
            )
            changes.append(f"  Reviewers: {reviewers}")
            continue

        try:
            # Check if already exists
            try:
                repo.get_environment(env_name)
                changes.append(
                    f"Environment '{env_name}' already exists in {repo.full_name} "
                    f"- skipping (no update support)"
                )
                continue
            except GithubException as check_e:
                if check_e.status != 404:
                    raise check_e

            # Create new environment
            repo.create_environment(
                environment_name=env_name,
                wait_timer=wait_timer,
                reviewers=reviewers if reviewers else None,
                deployment_branch_policy=branch_policy
            )
            changes.append(f"Created environment '{env_name}' in {repo.full_name}")

        except GithubException as e:
            changes.append(
                f"GitHub API error creating '{env_name}' in {repo.full_name}: {e}"
            )
            logger.error(f"API error details: {e}")

        except Exception as e:
            changes.append(
                f"Unexpected error creating '{env_name}' in {repo.full_name}: {e}"
            )
            logger.error(f"Unexpected error: {e}")

    return changes
