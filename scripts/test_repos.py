# scripts/test_repos.py
"""
Test script for running MCD enforcement on repositories.
- Discovers repos
- Runs file, branch protection, environment, and webhook enforcement
- Generates compliance report
"""

from typing import List
import logging

from .get_repos import get_repos
from .config_files import ensure_required_files
from .branch_protection import enforce_branch_protection
from .environments import enforce_environments
from .webhooks import enforce_webhooks
from .reporting import generate_report, save_and_print_report

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Main test flow
# -------------------------------------------------------------------
print("=== All repos mode (discovery only) ===")
repos = get_repos()
print(f"Found {len(repos)} repositories")
if repos:
    print("First few:", [r.full_name for r in repos[:5]])

print("\n=== Single repo mode (full enforcement) ===")
test_repo_name = "mcd-framework-test"
repos_single = get_repos(single_repo_name=test_repo_name)
print(f"Found {len(repos_single)} repositories matching '{test_repo_name}'")

if not repos_single:
    print(f"ERROR: Repository '{test_repo_name}' not found or inaccessible.")
else:
    repo = repos_single[0]
    print(f"Processing repository: {repo.full_name}")
    print(f"  Private: {repo.private}")
    print(f"  Default branch: {repo.default_branch}")
    print(f"  Archived: {repo.archived}")

    print("\n=== Running full enforcement (dry-run) ===")
    all_changes: List[str] = []

    # 1. Required config files
    print("\n→ Enforcing required files...")
    try:
        file_changes = ensure_required_files(repo, dry_run=False)
        all_changes.extend(file_changes)
        for msg in file_changes:
            print(f"  {msg}")
    except Exception as e:
        print(f"  ERROR in file enforcement: {e}")

    # 2. Branch protection & PR rules
    print("\n→ Enforcing branch protection & PR rules...")
    try:
        bp_changes = enforce_branch_protection(repo, dry_run=False)
        all_changes.extend(bp_changes)
        for msg in bp_changes:
            print(f"  {msg}")
    except Exception as e:
        print(f"  ERROR in branch protection: {e}")

    # 3. Environments (qual/prod)
    print("\n→ Enforcing environments...")
    try:
        env_changes = enforce_environments(repo, dry_run=False)
        all_changes.extend(env_changes)
        for msg in env_changes:
            print(f"  {msg}")
    except Exception as e:
        print(f"  ERROR in environments: {e}")

    # 4. Webhooks
    print("\n→ Enforcing webhooks...")
    try:
        webhook_changes = enforce_webhooks(repo, dry_run=False)
        all_changes.extend(webhook_changes)
        for msg in webhook_changes:
            print(f"  {msg}")
    except Exception as e:
        print(f"  ERROR in webhooks: {e}")

    # 5. Generate compliance report
    print("\n=== Generating & Saving Compliance Report ===")
    report = generate_report(
        repo_name=repo.name,
        changes=all_changes,
        dry_run=False
    )
    saved_path = save_and_print_report(report)
    print(f"Full report saved to: {saved_path}")