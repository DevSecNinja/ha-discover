# hadiscover

**hadiscover** is a search engine for Home Assistant automations hosted on GitHub. It allows you to discover, explore, and learn from automations created by the Home Assistant community.

## What is hadiscover?

hadiscover indexes Home Assistant automation files from GitHub repositories that opt in by adding the `hadiscover` or `ha-discover` topic to their repository. It provides a simple, searchable interface to find automations by name, description, trigger types, or related repositories.

Think of it as a specialized search engine for Home Assistant configurations—similar to how kubesearch.dev works for Kubernetes resources, but focused specifically on Home Assistant automations.

[Try it out now!](https://hadiscover.com/)

## Why hadiscover?

Home Assistant users often create sophisticated automations and share them on GitHub, but discovering these automations can be challenging. hadiscover solves this by:

- **Centralizing Discovery**: Aggregating automations from multiple repositories into one searchable index
- **Facilitating Learning**: Helping users learn from real-world automation examples
- **Promoting Sharing**: Encouraging the community to share their automations by making them easily discoverable
- **Opt-in Design**: Respecting privacy by only indexing repositories that explicitly opt in

## Features

- 🔍 **Full-text Search**: Search automations by name, description, trigger types, and repository information
- 📊 **Statistics Dashboard**: View total repositories and automations indexed
- 🔄 **Automated Indexing**: Daily scheduled indexing to discover newly added repositories (manual trigger available in development mode)
- 🔗 **Direct GitHub Links**: Every automation links directly to its source on GitHub
- 🎨 **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- ⚡ **Fast API**: RESTful API powered by FastAPI for quick searches
- 🐳 **Docker Ready**: Pre-built Docker images available via GitHub Container Registry
- 🔧 **Auto-Updates**: Renovate bot keeps dependencies automatically up-to-date

## How It Works

1. **Repository Discovery**: hadiscover searches GitHub for repositories with the `hadiscover` or `ha-discover` topic
2. **Automation Extraction**: For each repository, it locates automation files (e.g., `automations.yaml`)
3. **Parsing**: Automations are parsed using best-effort YAML parsing to extract metadata
4. **Indexing**: Automations are stored in a SQLite database with full-text search capability
5. **Search Interface**: Users can search through the indexed automations via a web UI

## Getting Started

### Quick Start with Docker

The easiest way to run hadiscover is using Docker:

```bash
# Using pre-built images from GitHub Container Registry
docker-compose -f docker-compose.prod.yml up -d

# Or build locally
docker-compose up -d
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Adding Your Repository

To have your Home Assistant configuration indexed:

1. Ensure your repository contains automation files (e.g., `automations.yaml`)
2. Add the `hadiscover` or `ha-discover` topic to your GitHub repository:
   - Go to your repository on GitHub
   - Click the ⚙️ icon next to "About"
   - Add `hadiscover` (or `ha-discover` for backwards compatibility) to the topics list
   - Save changes
3. Wait for the next scheduled indexing (runs daily at 2 AM UTC) or trigger it manually in development mode

## Develop a new feature

### Prerequisites

- **Backend**: Python 3.12+, pip
- **Frontend**: Node.js 18+, npm
- **Optional**: GitHub Personal Access Token (for higher API rate limits)

### Running Locally

#### 1. Clone the Repository

```bash
git clone https://github.com/DevSecNinja/hadiscover.git
cd hadiscover
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

### Docker Container Tests

Docker containers are automatically tested on every PR and push to main:

- Backend container build and health checks
- Frontend container build and health checks
- API endpoint functionality
- Security headers validation
- Integration test with both containers

See `.github/workflows/docker-test.yml` for details.

## Deployment

hadiscover can be deployed in various ways:

### Docker Deployment (Recommended)

See [RELEASES.md](./RELEASES.md) for information about:
- Using pre-built Docker images from GHCR
- Semantic versioning
- Release process
- Docker image tags

### GitHub Pages (Frontend Only)

The frontend can be deployed to GitHub Pages. See the existing `.github/workflows/deploy.yml` workflow.

## Architecture

For detailed information about the system architecture, data flow, and design decisions, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Contributing

Contributions are welcome! Whether it's bug fixes, feature enhancements, or documentation improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Acknowledgments

- Inspired by [kubesearch.dev](https://kubesearch.dev)
- Built with [FastAPI](https://fastapi.tiangolo.com/), [Next.js](https://nextjs.org/), and [Tailwind CSS](https://tailwindcss.com/)
- Powered by the [GitHub REST API](https://docs.github.com/en/rest)

## Support

If you find hadiscover useful, consider:

- ⭐ Starring the repository on GitHub
- 🐛 Reporting bugs or suggesting features via GitHub Issues
- 📢 Sharing with the Home Assistant community

**Happy Automating! 🏠✨**
