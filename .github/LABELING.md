# Automated Labeling Strategy

This repository uses automated labeling for Pull Requests and Issues to improve organization and make it easier to identify the scope of changes.

## Pull Request Labels

PRs are automatically labeled based on the files changed:

- **frontend** - Changes to Next.js/TypeScript frontend code in `frontend/` directory
- **backend** - Changes to Python/FastAPI backend code in `backend/` directory
- **dependencies** - Updates to dependencies (package.json, requirements.txt, etc.)
- **ci/cd** - Changes to GitHub Actions workflows or CI/CD scripts
- **documentation** - Changes to Markdown documentation files
- **docker** - Changes to Docker configuration files (Dockerfile, docker-compose.yml)
- **tests** - Changes to test files or test configuration
- **configuration** - Changes to configuration files (linters, git config, etc.)

### PR Labeler - How It Works

The PR labeler runs automatically when a PR is:
- Opened
- Updated (new commits pushed)
- Reopened

It uses the `.github/labeler.yml` configuration to match file paths to labels. The `sync-labels` option ensures labels are updated as the PR evolves.

## Issue Labels

Issues are automatically labeled based on keywords in the title and body:

- **frontend** - Keywords: frontend, ui, interface, next.js, react, typescript, css, tailwind
- **backend** - Keywords: backend, api, fastapi, python, database, sqlite, endpoint, service
- **docker** - Keywords: docker, container, image, dockerfile, docker-compose
- **ci/cd** - Keywords: ci/cd, workflow, github actions, deployment, pipeline
- **documentation** - Keywords: documentation, readme, docs, guide, tutorial
- **bug** - Keywords: bug, error, crash, fail, broken, issue, problem, not working
- **enhancement** - Keywords: feature, enhancement, improvement, add, new, request, suggestion
- **security** - Keywords: security, vulnerability, cve, exploit, unsafe
- **performance** - Keywords: performance, slow, optimize, speed, latency, memory
- **dependencies** - Keywords: dependency, dependencies, package, npm, pip, upgrade, update version

### Issue Labeler - How It Works

The issue labeler runs automatically when an issue is:
- Opened
- Edited

It uses a GitHub Actions script to scan the issue title and body for relevant keywords and applies matching labels.

## Manual Label Management

While most labels are applied automatically, maintainers can still:
- Add additional labels manually
- Remove auto-applied labels if incorrect
- Create custom labels for special cases

## Benefits

1. **Quick Identification**: See at a glance what areas of the codebase a PR affects
2. **Better Organization**: Filter and search issues/PRs by component
3. **Review Assignment**: Easily identify which team members should review
4. **Release Notes**: Generate better changelogs grouped by component
5. **Consistency**: Standardized labeling across all contributions

## Configuration Files

- `.github/labeler.yml` - PR labeling rules (path-based)
- `.github/workflows/auto-label.yml` - PR labeling workflow
- `.github/workflows/auto-label-issues.yml` - Issue labeling workflow

## Customization

To modify the labeling rules:

1. Edit `.github/labeler.yml` for PR path-based rules
2. Edit `.github/workflows/auto-label-issues.yml` to adjust issue keyword matching
3. Test changes by creating a PR or issue

For more information on the labeler syntax, see:
- [actions/labeler documentation](https://github.com/actions/labeler)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
