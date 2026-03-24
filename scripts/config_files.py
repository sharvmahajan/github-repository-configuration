# scripts/config_files.py
"""
Enforces presence of required config files in repositories.
Loads configuration from global.yaml and creates missing files from templates.
Supports Jinja2 templating with repo context.
Commits changes when dry_run=False.
"""

from typing import List, Dict, Any
from github import Repository, GithubException
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateError

from .github_client import get_github_client
from .config_loader import load_required_files

logger = logging.getLogger(__name__)

# Path to templates (relative to project root)
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Jinja2 environment (lazy-loaded, safe defaults)
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=True,          # safer for text/YAML/JSON
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render a Jinja2 template with provided context."""
    try:
        template = jinja_env.get_template(template_name)
        return template.render(**context)
    except TemplateNotFound:
        logger.error(f"Template file not found: {template_name}")
        raise
    except TemplateError as e:
        logger.error(f"Jinja2 rendering error in {template_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error rendering {template_name}: {e}")
        raise


def ensure_config_files(
    repo: Repository.Repository,
    files_config: List[Dict[str, str]],
    branch: str = "main",
    dry_run: bool = True,
) -> List[str]:
    """
    Internal helper: Ensures specified config files exist in the repo.
    Renders templates with Jinja2 using repo context.
    """
    changes = []

    if not repo.default_branch:
        changes.append(f"Repo {repo.full_name} has no default branch - skipping")
        return changes

    if branch != repo.default_branch:
        changes.append(f"Branch {branch} is not default ({repo.default_branch}) - skipping for safety")
        return changes

    # Context for Jinja2 rendering
    context = {
        "repo_name": repo.name,
        "repo_full_name": repo.full_name,
        "default_branch": repo.default_branch,
        "is_private": repo.private,
        "owner": repo.owner.login,
        "owner_type": "user" if not repo.organization else "org",
        # Add more context variables as needed
    }

    for cfg in files_config:
        path = cfg["path"]
        template_name = cfg.get("template")
        if not template_name:
            changes.append(f"Missing 'template' key for path {path} in {repo.full_name}")
            continue

        commit_msg = cfg.get("commit_message", f"Add required config: {path} [MCD Enforcer]")

        try:
            # Check if file already exists
            repo.get_contents(path, ref=branch)
            changes.append(f"{path} already exists in {repo.full_name}")
            continue
        except GithubException as e:
            if e.status != 404:
                changes.append(f"Error checking {path} in {repo.full_name}: {e}")
                continue

        # File missing → render and create
        try:
            content = render_template(template_name, context)
        except Exception as e:
            changes.append(f"Failed to render template {template_name} for {path} in {repo.full_name}: {e}")
            continue

        if dry_run:
            changes.append(f"[DRY-RUN] Would create {path} in {repo.full_name} with rendered content")
            continue

        try:
            repo.create_file(
                path=path,
                message=commit_msg,
                content=content,
                branch=branch,
            )
            changes.append(f"Created {path} in {repo.full_name}")
        except GithubException as e:
            changes.append(f"GitHub API error creating {path} in {repo.full_name}: {e}")
        except Exception as e:
            changes.append(f"Unexpected error creating {path} in {repo.full_name}: {e}")

    return changes


def ensure_required_files(
    repo: Repository.Repository,
    branch: str = "main",
    dry_run: bool = True,
) -> List[str]:
    """
    Public function: Enforce all required files defined in global.yaml.
    Automatically loads config and applies Jinja2 rendering.
    """
    files_config = load_required_files()

    if not files_config:
        msg = f"No 'required_files' defined in global.yaml for repo {repo.full_name}"
        logger.warning(msg)
        return [msg]

    logger.info(f"Enforcing {len(files_config)} required files for {repo.full_name} (dry_run={dry_run})")
    return ensure_config_files(repo, files_config, branch=branch, dry_run=dry_run)