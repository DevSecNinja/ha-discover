# Deployment to GitHub Pages

This document explains how to deploy the HA Discover frontend to GitHub Pages.

## ⚠️ Prerequisites

**Before deploying the frontend, you must first deploy the backend API.** GitHub Pages only hosts static files and cannot run the Python backend.

👉 **See [BACKEND_DEPLOYMENT.md](./BACKEND_DEPLOYMENT.md) for backend deployment instructions.**

## Quick Start

1. **Deploy backend** (see [BACKEND_DEPLOYMENT.md](./BACKEND_DEPLOYMENT.md))
2. **Get backend URL** (e.g., `https://your-app.railway.app`)
3. **Configure API URL** (see [Configure API URL](#2-configure-api-url) below)
4. **Enable GitHub Pages** (see [Enable GitHub Pages](#1-enable-github-pages) below)
5. **Push to main** to trigger deployment

## Configuration

The frontend is configured for static export to GitHub Pages with the following settings:

- **Output**: Static export (`output: 'export'` in `next.config.ts`)
- **Images**: Unoptimized (GitHub Pages doesn't support Next.js Image Optimization)
- **Base Path**: Can be configured if deploying to a repository subdirectory

## GitHub Actions Workflow

The deployment is automated via GitHub Actions (`.github/workflows/deploy.yml`):

1. **Triggers**: Runs on push to `main` branch or manual workflow dispatch
2. **Test**:
   - Sets up Python 3.12 environment
   - Installs backend dependencies
   - Runs all 23 backend tests with pytest
   - Deployment continues only if all tests pass
3. **Build**:
   - Installs Node.js dependencies
   - Builds the Next.js static export
   - Creates the `out/` directory with static files
4. **Deploy**:
   - Uploads artifacts to GitHub Pages
   - Deploys to the configured GitHub Pages URL

The workflow ensures code quality by running the full test suite before every deployment.

## Setup Instructions

### 1. Enable GitHub Pages

1. Go to your repository settings
2. Navigate to **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions**
4. Save the settings

### 2. Configure API URL

The workflow uses an environment variable for the API URL. You have two options:

**Option A: Update the workflow file** (recommended for testing)

Edit `.github/workflows/deploy.yml` and update the `NEXT_PUBLIC_API_URL`:

```yaml
env:
  NEXT_PUBLIC_API_URL: https://your-backend-api.com/api/v1
```

**Option B: Use GitHub Secrets** (recommended for production)

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Add a new repository secret: `API_URL`
3. Update the workflow to use the secret:

```yaml
env:
  NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}
```

### 3. Deploy

#### Automatic Deployment

Push to the `main` branch:

```bash
git push origin main
```

#### Manual Deployment

1. Go to **Actions** tab in your repository
2. Select the **Deploy to GitHub Pages** workflow
3. Click **Run workflow**
4. Select the branch and click **Run workflow**

### 4. Access Your Site

After successful deployment, your site will be available at:

```
https://<username>.github.io/<repository-name>/
```

For example: `https://devsecninja.github.io/hadiscover/`

## Base Path Configuration

The site uses a `basePath` in `next.config.ts` for GitHub Pages deployment:

```typescript
const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  basePath: '/ha-discover',  // Repository subdirectory path
};
```

**Important**: The `basePath` must match your repository structure for GitHub Pages to work correctly. If you fork this repository or deploy to a different location, update the `basePath` accordingly and rebuild before deploying.

## Troubleshooting

### Build Fails

- Check that `NEXT_PUBLIC_API_URL` is set correctly
- Ensure all dependencies are listed in `package.json`
- Review the Actions log for specific error messages

### 404 Errors

- Verify GitHub Pages is enabled in repository settings
- Check that the source is set to **GitHub Actions**
- Ensure the `basePath` matches your repository structure

### API Connection Issues

- Verify the API URL is accessible from the client
- Check CORS settings on your backend API
- Ensure the API URL uses HTTPS for production

## Local Testing of Static Export

To test the static export locally:

```bash
cd frontend
npm run build
npx serve out
```

This will serve the static files on `http://localhost:3000`.

## Backend Deployment

**Important**: GitHub Pages only hosts static frontend files. You must deploy the backend API separately to a hosting service.

For detailed backend deployment instructions, see **[BACKEND_DEPLOYMENT.md](./BACKEND_DEPLOYMENT.md)**.

### Quick Backend Deployment Options

The backend can be deployed to:

- **Docker** - Self-hosted or cloud deployment

After deploying your backend:

1. Get your backend URL (e.g., `https://your-app.railway.app`)
2. Update the `NEXT_PUBLIC_API_URL` in `.github/workflows/deploy.yml` (see below)
3. Push changes to trigger frontend deployment

See **[BACKEND_DEPLOYMENT.md](./BACKEND_DEPLOYMENT.md)** for step-by-step instructions.
