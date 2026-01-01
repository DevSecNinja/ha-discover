# hadiscover

A search engine for discovering Home Assistant automations shared on GitHub.

[Try it now at hadiscover.com](https://hadiscover.com/)

## What is it?

hadiscover indexes Home Assistant automation files from GitHub repositories that opt in by adding the `hadiscover` topic. Search by name, description, trigger types, or repository to find real-world automation examples.

## Why use it?

- **Discover**: Find automations from the Home Assistant community in one place
- **Learn**: See how others solve similar automation challenges
- **Share**: Make your automations discoverable by adding the `hadiscover` topic
- **Privacy**: Opt-in only—your repos are indexed only if you add the topic

## Features

- Full-text search across automations and repositories
- Filter by trigger types, blueprints, and repositories
- Direct GitHub links with precise line numbers
- Hourly automated indexing for fresh results
- Modern responsive UI with dark mode
- RESTful API with OpenAPI documentation

## Adding Your Repository

To have your automations indexed:

1. Ensure your repository has an `automations.yaml` file
2. Add the `hadiscover` topic to your GitHub repository:
   - Go to your repository on GitHub
   - Click the ⚙️ icon next to "About"
   - Add `hadiscover` to the topics list
   - Save changes
3. Wait for the next hourly indexing (or trigger manually in development mode)

---

## Development

### Prerequisites

- Python 3.12+, pip, venv
- Node.js 18+, npm
- Optional: GitHub Personal Access Token (for 5k/hr rate limit vs 60/hr)

### Quick Setup

```bash
git clone https://github.com/DevSecNinja/hadiscover.git
cd hadiscover

# Automated setup (installs backend and frontend dependencies)
./setup.sh

# Start both backend and frontend
./start.sh
```

Access the app:

- **Frontend**: <http://localhost:8080>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

Stop services:

```bash
./stop.sh
```

### Manual Setup

If you prefer manual setup or the scripts don't work:

**Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend (new terminal):**

```bash
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
# Pre-built images from GHCR
docker-compose -f docker-compose.prod.yml up -d

# Or build locally
docker-compose up -d
```

### Testing

Run backend tests:

```bash
cd backend && source venv/bin/activate && pytest tests/ -v
```

CI automatically tests Docker containers, API endpoints, and integration on every PR.

### API Documentation

OpenAPI/Swagger docs available at <http://localhost:8000/docs> once running.

**Key Endpoints:**

- `GET /api/v1/search?q={query}` - Search automations (with filters for repo, blueprint, trigger)
- `GET /api/v1/statistics` - Get totals and last indexed time
- `POST /api/v1/index` - Trigger indexing (dev mode only, rate limited)
- `GET /api/v1/health` - Health check

## More Information

- **Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details
- **Contributing**: PRs welcome! Open an issue for bugs or feature requests. PRs are automatically labeled based on changed files—see [.github/LABELING.md](./.github/LABELING.md) for details
- **License**: MIT License
- **Stack**: FastAPI (Python), Next.js (TypeScript), SQLite
- **Inspired by**: [kubesearch.dev](https://kubesearch.dev)

---

⭐ Star the repo if you find it useful | 🐛 Report bugs via GitHub Issues | 📢 Share with the Home Assistant community
