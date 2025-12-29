# Release Process

This document describes the release process for HA Discover, including versioning, Docker image creation, GitHub releases, and dependency management.

## Versioning Strategy

HA Discover follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New functionality in a backwards-compatible manner
- **PATCH** version (0.0.X): Backwards-compatible bug fixes

## Dependency Management

HA Discover uses [Renovate Bot](https://docs.renovatebot.com/) to automatically keep dependencies up-to-date.

### How Renovate Works

- **Automatic Updates**: Renovate checks for dependency updates every 6 hours
- **Pull Requests**: Creates PRs for outdated dependencies
- **Grouping**: Minor and patch updates are grouped together for easier review
- **Security**: Security updates are prioritized and labeled appropriately
- **Automerge**: Minor and patch updates can be automatically merged if tests pass

### Dependency Update Categories

1. **Python dependencies** (backend/requirements.txt)
   - Minor/patch updates: Auto-grouped and auto-merged
   - Major updates: Separate PRs, manual review required

2. **npm dependencies** (frontend/package.json)
   - Minor/patch updates: Auto-grouped and auto-merged
   - Major updates: Separate PRs, manual review required

3. **Docker base images** (Dockerfiles)
   - Patch updates: Auto-merged
   - Minor/major updates: Manual review required

4. **GitHub Actions** (workflows)
   - All updates: Auto-grouped and auto-merged

### Renovate Configuration

The Renovate configuration is located in `renovate.json`. Key features:

- **Dependency Dashboard**: View all pending updates in a single issue
- **Semantic Commits**: Uses conventional commit messages
- **Schedule**: Runs during off-peak hours (nights and weekends)
- **Rate Limiting**: Max 5 concurrent PRs, 2 per hour
- **Lock File Maintenance**: Monthly updates to lock files

### Manual Dependency Updates

If you need to update dependencies manually:

```bash
# Backend
cd backend
pip install --upgrade <package-name>
pip freeze > requirements.txt

# Frontend
cd frontend
npm update <package-name>
```

## Release Workflow

Releases are automated using GitHub Actions. The workflow handles:

1. Running tests to ensure code quality
2. Building Docker images for both backend and frontend
3. Pushing images to GitHub Container Registry (GHCR)
4. Creating a GitHub release with release notes
5. Tagging images with version numbers and `latest`

### Triggering a Release

There are two ways to trigger a release:

#### Method 1: Create and Push a Git Tag (Recommended)

```bash
# Create a new version tag (e.g., v0.1.0)
git tag v0.1.0

# Push the tag to GitHub
git push origin v0.1.0
```

The release workflow will automatically detect the tag and create a release.

#### Method 2: Manual Workflow Dispatch

1. Go to the [Actions tab](https://github.com/DevSecNinja/hadiscover/actions)
2. Select the "Release" workflow
3. Click "Run workflow"
4. Enter the version number (e.g., `0.1.0`) without the `v` prefix
5. Click "Run workflow"

### Configuring Frontend API URL

The frontend Docker image needs to know where the backend API is located. Configure this via GitHub repository variables:

1. Go to repository Settings → Secrets and variables → Actions → Variables
2. Create a new variable named `FRONTEND_API_URL`
3. Set the value to your backend API URL (e.g., `https://api.example.com/api/v1`)

If not configured, the frontend will default to `http://localhost:8000/api/v1`.

## Docker Images

Docker images are automatically built and pushed to GitHub Container Registry during the release process.

### Available Images

- **Backend**: `ghcr.io/devsecninja/hadiscover/backend`
- **Frontend**: `ghcr.io/devsecninja/hadiscover/frontend`

### Image Tags

Each release creates the following tags:

- `latest` - Always points to the most recent release
- `X.Y.Z` - Specific version (e.g., `0.1.0`)
- `X.Y` - Minor version (e.g., `0.1`)
- `X` - Major version (e.g., `0`)

### Pulling Images

```bash
# Pull the latest version
docker pull ghcr.io/devsecninja/hadiscover/backend:latest
docker pull ghcr.io/devsecninja/hadiscover/frontend:latest

# Pull a specific version
docker pull ghcr.io/devsecninja/hadiscover/backend:0.1.0
docker pull ghcr.io/devsecninja/hadiscover/frontend:0.1.0
```

### Using Images with Docker Compose

#### Production Deployment

Use the pre-built images from GHCR:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Or modify `docker-compose.yml` to use the image tags:

```yaml
services:
  api:
    image: ghcr.io/devsecninja/hadiscover/backend:latest
    # ... rest of config

  web:
    image: ghcr.io/devsecninja/hadiscover/frontend:latest
    # ... rest of config
```

#### Development

Build images locally:

```bash
docker-compose up -d
```

## Version Files

### Backend

Version information is stored in `/backend/app/version.py`:

```python
"""Version information for HA Discover backend."""

__version__ = "0.1.0"
```

The version is automatically updated during the release process and displayed in:
- API root endpoint (`/`)
- OpenAPI documentation (`/docs`)

### Frontend

Version information is stored in `/frontend/package.json`:

```json
{
  "name": "frontend",
  "version": "0.1.0",
  ...
}
```

## Pre-Release Checklist

Before creating a release, ensure:

- [ ] All tests pass (`pytest tests/ -v` in backend)
- [ ] Docker containers build and pass tests (check latest workflow run)
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated (if exists)
- [ ] Version numbers are appropriate for the changes
- [ ] Breaking changes are documented

## Continuous Integration

### Docker Container Testing

Every PR and push to main automatically:
- Builds both Docker images
- Tests container health checks
- Validates API endpoints
- Checks security headers
- Runs integration tests

See `.github/workflows/docker-test.yml` for the full test suite.

### Before Release

The release workflow includes all these checks plus:
- Full backend test suite
- Version file updates
- Multi-platform image builds

## Release Notes

GitHub releases automatically generate release notes from merged pull requests and commits. You can edit the release notes after creation to add:

- Highlights of major features
- Breaking changes with migration instructions
- Known issues
- Contributors acknowledgments

## Troubleshooting

### Release Workflow Fails

1. Check the [Actions tab](https://github.com/DevSecNinja/hadiscover/actions) for error details
2. Ensure all tests pass locally before creating a release
3. Verify that GitHub Actions has permission to write to GHCR

### Docker Image Not Found

1. Ensure the release workflow completed successfully
2. Check that you're using the correct image name and tag
3. For private repositories, authenticate with GHCR:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

### Version Mismatch

If version numbers don't match between backend and frontend:

1. Check the version in `backend/app/version.py`
2. Check the version in `frontend/package.json`
3. Manually update if necessary and create a new patch release

## Manual Release Process

If automated releases fail, you can manually create a release:

### 1. Update Version Files

Backend (`backend/app/version.py`):
```python
__version__ = "0.1.1"
```

Frontend (`frontend/package.json`):
```bash
cd frontend
npm version 0.1.1 --no-git-tag-version
```

### 2. Build and Push Docker Images

```bash
# Backend
cd backend
docker build -t ghcr.io/devsecninja/hadiscover/backend:0.1.1 .
docker push ghcr.io/devsecninja/hadiscover/backend:0.1.1

# Frontend
cd frontend
docker build -t ghcr.io/devsecninja/hadiscover/frontend:0.1.1 .
docker push ghcr.io/devsecninja/hadiscover/frontend:0.1.1
```

### 3. Create GitHub Release

1. Go to [Releases](https://github.com/DevSecNinja/hadiscover/releases)
2. Click "Draft a new release"
3. Create a new tag (e.g., `v0.1.1`)
4. Write release notes
5. Publish the release

## Support

For questions or issues with the release process, please [open an issue](https://github.com/DevSecNinja/hadiscover/issues).
