# GitHub MCD - Compliance & Configuration Enforcer

A comprehensive GitHub organization compliance and configuration management tool that automates the enforcement of branch protection rules, configuration files, and compliance standards across multiple repositories.

## 🎯 Overview

GitHub MCD (Mandatory Compliance Deployment) is designed to help organizations maintain consistent policies, security standards, and best practices across all GitHub repositories. It automates:

- **Branch Protection**: Enforces branch protection rules on default branches
- **Configuration Management**: Deploys and maintains required configuration files (APM.yaml, AI.yaml, Whitesource)
- **Compliance Reporting**: Generates detailed compliance reports with scoring
- **Team Management**: Supports organization-wide and team-specific enforcement
- **Webhooks**: Manages GitHub webhook configurations
- **Dry-Run Mode**: Preview changes before applying them

## ✨ Features

- ✅ **YAML-based Configuration**: Simple YAML configs for organization-wide policies
- ✅ **Multi-Repository Support**: Target single repos or entire organizations
- ✅ **Team-Based Deployment**: Deploy configs to specific team repositories
- ✅ **Dry-Run Mode**: Preview all changes before executing
- ✅ **Compliance Scoring**: Automatic compliance calculations with status reporting
- ✅ **JSON & PDF Reports**: Generate detailed compliance reports in multiple formats
- ✅ **Centralized GitHub Client**: Efficient API handling
- ✅ **Comprehensive Logging**: Detailed activity logs for audit trails

## 📋 Requirements

- Python 3.8+
- GitHub Personal Access Token with repo and admin permissions

### Dependencies

```
PyGithub==2.5.0              # GitHub API client
PyYAML==6.0.2               # YAML configuration parsing
python-dotenv==1.0.1        # Environment variable management
jinja2==3.1.6               # Template rendering
reportlab==3.6.13           # PDF report generation
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "GitHub MCD"
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate      # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy `.env.example` and configure it with your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your GitHub credentials:

```env
ENFORCER_TOKEN=your_github_personal_access_token
WEBHOOK_SECRET=your_webhook_secret_key
```

- **ENFORCER_TOKEN**: GitHub Personal Access Token with repo and admin permissions
- **WEBHOOK_SECRET**: Secret key for validating incoming webhooks

## ⚙️ Configuration

### Global Configuration (`config/global.yaml`)

The main configuration file controls organization-wide policies:

```yaml
organization: your-org-name

target_repos:
  - repo-name-1
  - repo-name-2

required_files:
  - path: .github/APM.yaml
    template: APM.yaml
    commit_message: "Add APM configuration [MCD Enforcer]"
  
  - path: .github/AI.yaml
    template: AI.yaml
    commit_message: "Add AI guidelines [MCD Enforcer]"

branch_protection:
  enabled: true
  branch: main
  required_approving_review_count: 1
  require_code_owner_reviews: true
  dismiss_stale_reviews: true
  enforce_admins: true
  required_status_checks:
    strict: true
    contexts:
      - "ci/build"
      - "security/scan"
```

### Teams Configuration (`config/teams.yaml`)

Configure team-specific repository assignments:

```yaml
teams:
  - name: backend
    repos:
      - backend-api
      - backend-services
  
  - name: frontend
    repos:
      - frontend-app
      - frontend-shared
```

### Configuration Templates (`templates/`)

Template files (`*.yaml`) are deployed to repositories as required files. Examples:

- `APM.yaml` - Application Performance Monitoring configuration
- `AI.yaml` - AI guidelines and policies
- `.whitesource` - Security scanning configuration

## 📖 Usage

### Load & Test Configuration

Validate your configuration files:

```bash
python -m scripts.test_config
```

### Test Repository Configuration in Single Go

```bash
python -m scripts.test_repos
```

### Enforce Branch Protection

Apply branch protection rules:

```bash
# Dry-run (preview changes)
python -m scripts.branch_protection --dry-run

# Apply changes
python -m scripts.branch_protection --apply
```

### Deploy Configuration Files

Deploy required configuration files to repositories:

```bash
# Dry-run
python -m scripts.config_files --dry-run

# Apply changes
python -m scripts.config_files --apply
```

### Manage Webhooks

Configure GitHub webhooks:

```bash
python -m scripts.webhooks --config config/webhook_mappings.yaml
```

### Generate Compliance Report

Create compliance report and scoring:

```bash
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (git-ignored)
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
│
├── config/
│   ├── global.yaml                 # Main organization configuration
│   ├── teams.yaml                  # Team-specific repo assignments
│   └── webhook_mappings.yaml       # Webhook event configurations
│
├── templates/
│   ├── APM.yaml                   # APM configuration template
│   ├── AI.yaml                    # AI guidelines template
│   └── .whitesource               # Security scanning template
│
├── scripts/
│   ├── __init__.py
│   ├── github_client.py           # Centralized GitHub API client
│   ├── config_loader.py           # Configuration file loading
│   ├── get_repos.py               # Repository retrieval logic
│   ├── branch_protection.py       # Branch protection enforcement
│   ├── config_files.py            # Configuration file deployment
│   ├── environments.py            # Environment management
│   ├── reporting.py               # Compliance report generation
│   ├── webhooks.py                # Webhook management
│   ├── test_config.py             # Config validation testing
│   └── test_repos.py              # Repository access testing
│
└── reports/
    └── compliance-report-*.json     # Generated compliance reports
```

## 🔧 Main Scripts

### `github_client.py`
Centralized GitHub API client with optimized authentication and rate limiting.

### `config_loader.py`
Loads and validates YAML configuration files with environment variable support.

### `get_repos.py`
Retrieves repositories based on organization, team, or individual repo filters.

### `branch_protection.py`
Enforces branch protection rules according to configuration with dry-run support.

### `config_files.py`
Deploys and maintains required configuration files across repositories.

### `reporting.py`
Generates compliance reports with scoring (0-100 scale) and status classification.

### `webhooks.py`
Manages GitHub webhook event subscriptions and configurations.

## 📊 Compliance Reports

Reports are automatically generated in the `reports/` directory with:

- **Compliance Score**: 0-100 scale
- **Status**: Compliant, Partially Compliant, Non-Compliant
- **Repository Details**: Status for each repository
- **Change Summary**: All enforcement actions taken
- **Timestamps**: ISO 8601 formatted report generation time

Output formats:
- **JSON**: Machine-readable compliance data
- **PDF**: Human-readable report document
- ✅ Use dry-run mode to preview changes before applying
- ✅ Review branch protection settings for your security requirements
- ✅ Audit webhook configurations regularly
- ✅ Keep token scope minimal (repo + admin for branch protection)
- ✅ Store `WEBHOOK_SECRET` securely and use it to validate webhook payloadsssions

## 🐛 Troubleshooting

### Authentication Issues
```bash
# Verify GITHUB_TOKEN is set correctly
echo $GITHUB_TOKEN
```

### Configuration Errors
```bash
# Test config loading
python -m scripts.test_config
```

### Repository Access Problems
```bash
# Check repository list and permissions
python -m scripts.test_repos
```

### Rate Limiting
- GitHub API has rate limits (60 req/hour unauthenticated, 5000/hour authenticated)
- Implement backoff strategies for large organizations
- Consider using GitHub App tokens for higher limits

## 📝 Logging

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

All operations are logged with timestamps for audit trails and debugging.

## 🤝 Contributing

When modifying scripts:

1. Test configuration with `test_config.py`
2. Test repositories with `test_repos.py`
3. Always use `--dry-run` mode first
4. Update documentation for new features
5. Maintain consistent code style with existing scripts

## 📄 License

This project is open source and available under the MIT License.


## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review configuration files for correctness
3. Check GitHub API documentation: https://docs.github.com/en/rest
4. Review PyGithub documentation: https://pypi.org/project/PyGithub/

---

**Last Updated**: March 2026  
**Version**: 1.0.0
