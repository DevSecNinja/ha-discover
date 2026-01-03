# Renovate Bot Configuration

This repository uses [Renovate Bot](https://docs.renovatebot.com/) to automatically keep dependencies up-to-date.

## Overview

Renovate automatically:

- Detects outdated dependencies
- Creates pull requests for updates
- Groups related updates together
- Prioritizes security updates
- Auto-merges safe updates (minor/patch versions)

## Setup

This repository uses the **managed Renovate GitHub App**. To enable it:

1. Install the Renovate app from the [GitHub Marketplace](https://github.com/apps/renovate)
2. Grant access to this repository
3. Renovate will automatically start using the configuration in `renovate.json`

No workflow files or tokens are needed - the managed app handles everything.

## Configuration

The main configuration is in [`renovate.json`](../renovate.json) at the repository root.

### Key Settings

- **Schedule**: Runs every 6 hours, preferring off-peak times (nights and weekends)
- **Rate Limiting**: Maximum 5 concurrent PRs, 2 per hour
- **Automerge**: Enabled for minor and patch updates
- **Dependency Dashboard**: Provides an overview of all pending updates
- **Security Updates**: Processed immediately, not subject to scheduling

### Package Rules

1. **Python Dependencies** (backend)
   - Minor/patch: Auto-grouped and auto-merged
   - Major: Separate PRs, manual review

2. **npm Dependencies** (frontend)
   - Minor/patch: Auto-grouped and auto-merged
   - Major: Separate PRs, manual review

3. **Docker Images**
   - Patch: Auto-merged
   - Minor/major: Manual review

4. **GitHub Actions**
   - All: Auto-grouped and auto-merged

## Dependency Dashboard

Renovate creates a "Dependency Dashboard" issue that shows:

- All detected dependencies
- Pending updates
- Rate-limited PRs
- Errored updates

Look for an issue titled "Dependency Dashboard" in the Issues tab.

## Disabling Renovate

To temporarily disable Renovate:

1. Add to `renovate.json`:

   ```json
   {
     "enabled": false
   }
   ```

2. Or close the Dependency Dashboard issue (will reopen when you want to re-enable)

## Security Updates

Security updates are:

- Processed immediately (not subject to schedule)
- Labeled with "security"
- Never auto-merged (require manual review)
- Created as separate PRs

## Lock File Maintenance

Lock file maintenance is enabled with automerge:

- Runs monthly (before 3am on the first day of the month)
- Automatically merges to keep lock files up-to-date
- Helps reduce security vulnerabilities and keeps dependencies consistent

## Dependency Tracking Details

### Fully Tracked Dependencies

Renovate automatically detects and tracks updates for:

- **Python packages** (`pip_requirements`): All packages in `backend/requirements.txt` and `requirements.txt`
- **npm packages**: All packages in `frontend/package.json`
- **Docker base images**: `python`, `node`, `nginx` in Dockerfiles
- **GitHub Actions**: All actions using `@v{major}` or `@v{major}.{minor}.{patch}` format
- **Pre-commit hooks**: All hooks in `.pre-commit-config.yaml`

### Partially Tracked Dependencies

Some dependencies are detected but may not always receive automatic updates:

#### 1. **Pre-commit Additional Dependencies**

- **Location**: `.pre-commit-config.yaml`
- **Example**: `additional_dependencies: ["@biomejs/biome@2.3.10"]`
- **Status**: Renovate detects these but may not always update them automatically
- **Recommendation**: Monitor the Dependency Dashboard for updates to these packages

#### 2. **Inline Version Numbers in GitHub Actions**

- **Location**: `.github/workflows/deploy.yml`, `.github/workflows/release.yml`
- **Examples**:
  - `python-version: "3.14"` (in `actions/setup-python@v6`)
  - `node-version: "24"` (in `actions/setup-node@v6`)
- **Status**: Renovate detects these as separate entries but doesn't use version tags
- **Note**: These follow the runtime versions (Python, Node.js) rather than action versions
- **Current Tracking**: Listed in Dependency Dashboard as `python 3.14` and `node 24`

#### 3. **Docker Images with `latest` Tag**

- **Location**: `docker-compose.prod.yml`
- **Examples**:
  - `ghcr.io/devsecninja/hadiscover/backend:latest`
  - `ghcr.io/devsecninja/hadiscover/frontend:latest`
- **Status**: Renovate is configured to suggest pinning to specific version tags
- **Configuration**: A package rule matches these images and will create PRs to replace `:latest` with versioned tags
- **Note**: Renovate will automatically detect available versions and suggest upgrades from `:latest` to specific version tags (e.g., `v1.0.0`)

### Previously Untracked (Now Fixed)

The following were not properly tracked but have been corrected:

#### 1. **GitHub Actions with Commit SHA**

- **Previous**: `softprops/action-gh-release@a06a81a03ee405af7f2048a818ed3f03bbf83c7b # v2`
- **Fixed to**: `softprops/action-gh-release@v2`
- **Reason**: Using commit SHAs prevents Renovate from detecting new versions
- **Solution**: Use version tags (e.g., `@v2`, `@v2.1.0`) instead of commit hashes

#### 2. **GitHub Actions with Branch Names**

- **Previous**: `aquasecurity/trivy-action@master`
- **Fixed to**: `aquasecurity/trivy-action@0.33.1`
- **Reason**: Using branch names (like `master` or `main`) prevents version tracking
- **Solution**: Use semantic version tags to enable proper update detection

### Best Practices for Dependency Management

To ensure Renovate can properly track and update dependencies:

1. **GitHub Actions**: Use version tags (`@v1`, `@v1.2.3`) instead of commit SHAs or branch names
2. **Docker Images**: Use specific version tags instead of `latest` for production
   - Renovate is configured to automatically suggest replacing `:latest` tags with versioned tags
   - When versioned tags are available, Renovate will create PRs to pin to specific versions
3. **Pre-commit Hooks**: Keep `additional_dependencies` versions in sync with main hook versions
4. **Lock Files**: Let Renovate handle lock file maintenance automatically (enabled with automerge)

## Customization

To modify Renovate's behavior, edit `renovate.json`. Common customizations:

### Change Schedule

```json
{
  "schedule": ["before 5am on monday"]
}
```

### Disable Automerge

```json
{
  "packageRules": [
    {
      "matchManagers": ["pip_requirements", "npm"],
      "automerge": false
    }
  ]
}
```

### Add More Reviewers

```json
{
  "reviewers": ["username1", "username2"]
}
```

## Troubleshooting

### Renovate Not Running

1. Check if the Renovate app is installed for this repository
2. Verify the app has the required permissions
3. Check the Dependency Dashboard issue for any errors

### Too Many PRs

Adjust rate limiting in `renovate.json`:

```json
{
  "prConcurrentLimit": 2,
  "prHourlyLimit": 1
}
```

### Renovate Stuck

1. Close and reopen the Dependency Dashboard issue
2. Check Renovate's debug logs (available in the dashboard issue)
3. Verify `renovate.json` syntax is valid

## Resources

- [Renovate Documentation](https://docs.renovatebot.com/)
- [Configuration Options](https://docs.renovatebot.com/configuration-options/)
- [Preset Configs](https://docs.renovatebot.com/presets/)
- [GitHub App Installation](https://github.com/apps/renovate)
