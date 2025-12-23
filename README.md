# HA Discover

**HA Discover** is a search engine for Home Assistant automations hosted on GitHub. It allows you to discover, explore, and learn from automations created by the Home Assistant community.

## What is HA Discover?

HA Discover indexes Home Assistant automation files from GitHub repositories that opt in by adding the `ha-discover` topic to their repository. It provides a simple, searchable interface to find automations by name, description, trigger types, or related repositories.

Think of it as a specialized search engine for Home Assistant configurations—similar to how kubesearch.dev works for Kubernetes resources, but focused specifically on Home Assistant automations.

## Why HA Discover?

Home Assistant users often create sophisticated automations and share them on GitHub, but discovering these automations can be challenging. HA Discover solves this by:

- **Centralizing Discovery**: Aggregating automations from multiple repositories into one searchable index
- **Facilitating Learning**: Helping users learn from real-world automation examples
- **Promoting Sharing**: Encouraging the community to share their automations by making them easily discoverable
- **Opt-in Design**: Respecting privacy by only indexing repositories that explicitly opt in

## Features

- 🔍 **Full-text Search**: Search automations by name, description, trigger types, and repository information
- 📊 **Statistics Dashboard**: View total repositories and automations indexed
- 🔄 **On-demand Indexing**: Trigger re-indexing to discover newly added repositories
- 🔗 **Direct GitHub Links**: Every automation links directly to its source on GitHub
- 🎨 **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- ⚡ **Fast API**: RESTful API powered by FastAPI for quick searches

## How It Works

1. **Repository Discovery**: HA Discover searches GitHub for repositories with the `ha-discover` topic
2. **Automation Extraction**: For each repository, it locates automation files (e.g., `automations.yaml`)
3. **Parsing**: Automations are parsed using best-effort YAML parsing to extract metadata
4. **Indexing**: Automations are stored in a SQLite database with full-text search capability
5. **Search Interface**: Users can search through the indexed automations via a web UI

## Getting Started

### Adding Your Repository

To have your Home Assistant configuration indexed:

1. Ensure your repository contains automation files (e.g., `automations.yaml`)
2. Add the `ha-discover` topic to your GitHub repository:
   - Go to your repository on GitHub
   - Click the ⚙️ icon next to "About"
   - Add `ha-discover` to the topics list
   - Save changes
3. Trigger indexing on HA Discover (or wait for the next scheduled index)

## Develop a new feature

### Prerequisites

- **Backend**: Python 3.12+, pip
- **Frontend**: Node.js 18+, npm
- **Optional**: GitHub Personal Access Token (for higher API rate limits)

### Running Locally

#### 1. Clone the Repository

```bash
git clone https://github.com/DevSecNinja/ha-discover.git
cd ha-discover
```

#### 2. Set Up the Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment variables
cp .env.example .env
# Edit .env to add your GITHUB_TOKEN if desired

# Run the backend server
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

#### 3. Set Up the Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# (Optional) Configure environment variables
cp .env.local.example .env.local

# Run the development server
npm run dev
```

The web UI will be available at `http://localhost:3000`

#### 4. Trigger Indexing

1. Open your browser to `http://localhost:3000`
2. Click the "Trigger Re-Index" button to start discovering repositories
3. Wait a few moments, then refresh to see the results

## API Documentation

The backend API is documented with OpenAPI/Swagger. Once the backend is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

- `GET /api/v1/search?q={query}` - Search for automations
- `GET /api/v1/statistics` - Get indexing statistics
- `POST /api/v1/index` - Trigger repository indexing (rate limited to once per 10 minutes)
- `GET /api/v1/health` - Health check

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

All tests should pass. The test suite includes:

- YAML parsing tests
- Search functionality tests
- API endpoint tests

## Architecture

For detailed information about the system architecture, data flow, and design decisions, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Deployment

### GitHub Pages Deployment

The frontend can be deployed to GitHub Pages for free hosting. See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

**Quick steps:**

1. Enable GitHub Pages in repository settings (Source: GitHub Actions)
2. Update the API URL in `.github/workflows/deploy.yml`
3. Push to `main` branch or manually trigger the workflow
4. Backend tests run automatically before deployment
5. Access your site at `https://<username>.github.io/<repository>/`

**Note**: You'll need to deploy the backend API separately to a hosting service (Heroku, Railway, Render, etc.) and configure the API URL in the deployment workflow. The deployment workflow runs all backend tests before deploying to ensure code quality.

## Contributing

Contributions are welcome! Whether it's bug fixes, feature enhancements, or documentation improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Acknowledgments

- Inspired by [kubesearch.dev](https://kubesearch.dev)
- Built with [FastAPI](https://fastapi.tiangolo.com/), [Next.js](https://nextjs.org/), and [Tailwind CSS](https://tailwindcss.com/)
- Powered by the [GitHub REST API](https://docs.github.com/en/rest)

## Support

If you find HA Discover useful, consider:

- ⭐ Starring the repository on GitHub
- 🐛 Reporting bugs or suggesting features via GitHub Issues
- 📢 Sharing with the Home Assistant community

**Happy Automating! 🏠✨**
