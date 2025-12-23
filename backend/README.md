# HA Discover Backend

This is the backend API for HA Discover, built with FastAPI.

## 🚀 Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

### Running Tests

```bash
pytest tests/ -v
```

## 🌐 Deployment

The backend must be deployed to a hosting platform that supports Python applications.

### Quick Deploy Options

- **Docker**: Uses `Dockerfile`

### Configuration Files

- `Dockerfile` - Docker container configuration

## 🔧 Configuration

### Environment Variables

- `GITHUB_TOKEN` (optional): GitHub Personal Access Token for higher API rate limits
- `ROOT_PATH` (optional): Base path for the API when deployed behind a reverse proxy or on cloud platforms (e.g., Azure Container Apps). Leave empty for default behavior.

Create a `.env` file:

```bash
cp .env.example .env
# Edit .env and add your GitHub token and other configuration
```

#### Deployment-Specific Configuration

**Azure Container Apps / Cloud Platforms:**

If you're deploying to Azure Container Apps or similar platforms where the application is accessed without the `/api/v1` prefix in the URL, you can set:

```bash
ROOT_PATH=/api/v1
```

This configures FastAPI to properly handle requests when the platform's routing layer strips or doesn't include the `/api/v1` prefix. Your application will then be accessible at the root URL (e.g., `https://your-app.azurecontainerapps.io/`) while maintaining the correct API path structure internally.

## 📚 API Endpoints

- `GET /api/v1/search?q={query}` - Search automations
- `GET /api/v1/statistics` - Get indexing statistics
- `POST /api/v1/index` - Trigger repository indexing
- `GET /api/v1/health` - Health check

## 🛠️ Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   │   ├── github_service.py
│   │   ├── parser.py
│   │   ├── indexer.py
│   │   └── search_service.py
│   └── api/
│       └── routes.py     # API endpoints
├── tests/                # Test suite
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration

```

## 🔒 CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:3000` (local frontend)
- `http://127.0.0.1:3000` (local frontend)
- `https://devsecninja.github.io` (production frontend)

If you fork the repository, update the CORS origins in `app/main.py`.

## 📖 Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [README.md](../README.md) - Project overview

## 🐛 Troubleshooting

### Database Issues

The app uses SQLite with the database stored in `data/ha_discover.db`. If you encounter database issues:

```bash
# Remove the database and restart
rm -rf data/
python -m uvicorn app.main:app --reload
```

### GitHub API Rate Limits

Without a token, GitHub limits you to 60 requests per hour. Add a `GITHUB_TOKEN` to increase this to 5,000 requests per hour.

### CORS Errors

If the frontend can't connect, ensure:
1. The backend is running and accessible
2. The CORS origins include your frontend URL
3. The frontend is using the correct API URL

## 📝 License

MIT License - see [LICENSE](../LICENSE) for details
