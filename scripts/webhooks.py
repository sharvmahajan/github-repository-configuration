# scripts/webhooks.py
"""
Enforces webhooks in repositories.
- Applies global webhooks from global.yaml
- Adds per-repo overrides from webhook_mappings.yaml
- Creates missing webhooks, skips if URL already exists
- Supports dry-run mode
- Handles secrets via {{ secrets.NAME }} placeholders (local .env fallback)
"""

from typing import List, Dict, Any
from github import Repository, GithubException
import logging
import os

from .github_client import get_github_client
from .config_loader import load_global_config, load_webhook_mappings

logger = logging.getLogger(__name__)


def enforce_webhooks(
    repo: Repository.Repository,
    dry_run: bool = True,
) -> List[str]:
    """
    Apply global + per-repo webhooks from config files.
    Skips creation if webhook with same URL already exists.
    """
    changes = []

    # Load configs
    global_hooks = load_global_config().get("webhooks_global", [])
    per_repo_hooks = load_webhook_mappings().get(repo.name, [])

    # Combine: per-repo overrides take precedence (by URL)
    all_hooks = global_hooks + per_repo_hooks

    if not all_hooks:
        msg = f"No webhooks defined for {repo.full_name}"
        logger.info(msg)
        changes.append(msg)
        return changes

    try:
        existing_hooks = list(repo.get_hooks())
        existing_urls = {h.config.get("url") for h in existing_hooks if h.config.get("url")}
    except GithubException as e:
        changes.append(f"Error fetching existing webhooks for {repo.full_name}: {e}")
        logger.error(f"Webhook fetch error: {e}")
        return changes

    for hook_cfg in all_hooks:
        url = hook_cfg.get("url")
        if not url:
            changes.append(f"Missing URL in webhook config for {repo.full_name}")
            continue

        events = hook_cfg.get("events", ["push", "pull_request"])
        secret_placeholder = hook_cfg.get("secret", "")
        content_type = hook_cfg.get("content_type", "json")
        active = hook_cfg.get("active", True)

        # Resolve secret
        real_secret = ""
        if secret_placeholder.startswith("{{ secrets."):
            secret_name = secret_placeholder.split("{{ secrets.")[1].split(" }}")[0].strip()
            real_secret = os.getenv(secret_name, "")
            if not real_secret:
                logger.warning(f"Secret '{secret_name}' not found in .env - webhook {url} will be created without secret")
        else:
            real_secret = secret_placeholder

        # Check if webhook with this URL already exists
        if url in existing_urls:
            changes.append(f"Webhook {url} already exists in {repo.full_name} - skipping")
            continue

        if dry_run:
            changes.append(f"[DRY-RUN] Would create webhook {url} in {repo.full_name}")
            changes.append(f"  - Events: {events}")
            changes.append(f"  - Active: {active}")
            changes.append(f"  - Content type: {content_type}")
            changes.append("  - Secret: [REDACTED]" if real_secret else "  - Secret: none")
            continue

        try:
            repo.create_hook(
                name="web",
                config={
                    "url": url,
                    "content_type": content_type,
                    "secret": real_secret,
                    "insecure_ssl": "0"  # secure SSL (1 = insecure, 0 = verify)
                },
                events=events,
                active=active
            )
            changes.append(f"Created webhook {url} in {repo.full_name}")
        except GithubException as e:
            changes.append(f"Failed to create webhook {url} in {repo.full_name}: {e}")
            logger.error(f"Webhook creation error: {e}")

    return changes