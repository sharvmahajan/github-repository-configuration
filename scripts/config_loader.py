# scripts/config_loader.py
"""
Centralized loader for all YAML configuration files.
All other modules should import these functions instead of loading YAML directly.
"""

import os
import yaml
from pathlib import Path
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Base directory for config files (relative to project root)
CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_yaml(file_path: Path, default: Any = None) -> Any:
    """
    Safe helper to load a YAML file.
    Returns default if file missing or invalid.
    """
    if not file_path.exists():
        logger.warning(f"Config file not found: {file_path}. Using default.")
        return default or {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.debug(f"Loaded config from {file_path}")
        return data or {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {file_path}: {e}")
        return default or {}
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return default or {}


def load_global_config() -> Dict[str, Any]:
    """
    Loads the main global configuration.
    Expected keys: organization, branch_protection, required_files, environments,
                   webhooks (global), pr_reviews, etc.
    """
    path = CONFIG_DIR / "global.yaml"
    return _load_yaml(path, default={})


def load_teams_config() -> Dict[str, str]:
    """
    Loads team slug → permission mappings.
    Example structure:
    teams:
      dev-team: push
      security-team: admin
    Returns dict like {"dev-team": "push", ...}
    """
    path = CONFIG_DIR / "teams.yaml"
    raw = _load_yaml(path, default={})
    return raw.get("teams", {})


def load_webhook_mappings() -> Dict[str, List[Dict[str, Any]]]:
    """
    Loads per-repo webhook overrides.
    Example structure:
    repo-name:
      - url: https://example.com/hook
        events: [push, pull_request]
        secret: some-secret
    Returns dict like {"repo-name": [{...}, ...]}
    """
    path = CONFIG_DIR / "webhook_mappings.yaml"
    return _load_yaml(path, default={})


def get_all_configs() -> Dict[str, Any]:
    """
    Convenience: Load everything at once.
    Useful in main.py or for validation.
    """
    return {
        "global": load_global_config(),
        "teams": load_teams_config(),
        "webhook_mappings": load_webhook_mappings(),
    }

def load_required_files() -> List[Dict[str, str]]:
    """
    Load the required_files list from global.yaml.
    Returns empty list if not defined.
    """
    global_config = load_global_config()
    return global_config.get("required_files", [])