# Fly.io + Neon Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the TGIS Phishing URL Detection system publicly at `https://tgis-dashboard.fly.dev` with zero cold starts, a live PostgreSQL database on Neon, and real Google Safe Browsing checks.

**Architecture:** Two always-on Fly.io machines (API on port 8000, Dashboard on port 8501) communicate over HTTPS. FastAPI connects to Neon's serverless PostgreSQL via `DATABASE_URL`. Four targeted code changes make the app production-aware: configurable API URL, real Safe Browsing, env-driven CORS, and `ALLOWED_ORIGIN` in settings.

**Tech Stack:** Fly.io (Docker-based PaaS), Neon (serverless PostgreSQL), Google Safe Browsing API v4, Docker (python:3.12-slim), Python 3.12

---

## File Map

| Action | File | Purpose |
|---|---|---|
| Modify | `src/core/config.py` | Add `ALLOWED_ORIGIN` setting |
| Modify | `api/main.py` | Use `ALLOWED_ORIGIN` for CORS instead of `*` |
| Modify | `src/external/safe_browsing.py` | Replace mock with real HTTP call |
| Modify | `dashboard/utils/api_client.py` | Read `API_BASE_URL` from env |
| Create | `.dockerignore` | Keep Docker images lean |
| Create | `Dockerfile.api` | Build image for FastAPI backend |
| Create | `Dockerfile.dashboard` | Build image for Streamlit frontend |
| Create | `fly.api.toml` | Fly.io config for API (port 8000, always-on) |
| Create | `fly.dashboard.toml` | Fly.io config for Dashboard (port 8501, always-on) |
| Modify | `.env.example` | Document new env vars |
| Create | `tests/test_deployment_config.py` | Tests for all four code changes |

---

## Task 1: Add `ALLOWED_ORIGIN` to Settings

**Files:**
- Modify: `src/core/config.py`
- Test: `tests/test_deployment_config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_deployment_config.py`:

```python
import pytest
from src.core.config import Settings


def test_allowed_origin_defaults_to_localhost():
    s = Settings()
    assert s.ALLOWED_ORIGIN == "http://localhost:8501"


def test_allowed_origin_reads_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://tgis-dashboard.fly.dev")
    s = Settings()
    assert s.ALLOWED_ORIGIN == "https://tgis-dashboard.fly.dev"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_deployment_config.py::test_allowed_origin_defaults_to_localhost -v
```

Expected: `FAILED` — `Settings` has no `ALLOWED_ORIGIN` attribute yet.

- [ ] **Step 3: Add `ALLOWED_ORIGIN` to `src/core/config.py`**

Open `src/core/config.py`. After the `SECRET_KEY` block (around line 37), add:

```python
    # CORS
    ALLOWED_ORIGIN: str = Field(default="http://localhost:8501", env="ALLOWED_ORIGIN")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_deployment_config.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/core/config.py tests/test_deployment_config.py
git commit -m "feat: add ALLOWED_ORIGIN to settings"
```

---

## Task 2: Fix CORS in `api/main.py`

**Files:**
- Modify: `api/main.py`
- Test: `tests/test_deployment_config.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_deployment_config.py`:

```python
from fastapi.testclient import TestClient
from api.main import app


def test_cors_allows_localhost_8501():
    """Verify localhost:8501 (default ALLOWED_ORIGIN) is in the CORS allowed list."""
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert "access-control-allow-origin" in response.headers


def test_cors_blocks_arbitrary_origin():
    """Verify a random origin is not echoed back."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.com"}
    )
    allow = response.headers.get("access-control-allow-origin", "")
    assert allow != "https://evil.com"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_deployment_config.py::test_cors_blocks_arbitrary_origin -v
```

Expected: `FAILED` — current wildcard `*` echoes back any origin.

- [ ] **Step 3: Update CORS middleware in `api/main.py`**

Replace the existing `CORSMiddleware` block (lines 25–31):

```python
from src.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN, "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_deployment_config.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add api/main.py tests/test_deployment_config.py
git commit -m "fix: tighten CORS to ALLOWED_ORIGIN instead of wildcard"
```

---

## Task 3: Wire Real Google Safe Browsing API

**Files:**
- Modify: `src/external/safe_browsing.py`
- Test: `tests/test_deployment_config.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_deployment_config.py`:

```python
from unittest.mock import patch, MagicMock
from src.external.safe_browsing import SafeBrowsingClient


def test_safe_browsing_detects_threat():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "matches": [{"threatType": "SOCIAL_ENGINEERING", "platformType": "ANY_PLATFORM"}]
    }
    with patch("requests.post", return_value=mock_resp):
        client = SafeBrowsingClient(api_key="test_key")
        result = client.check_url("http://phishing.example.com")
    assert result["is_threat"] is True
    assert "SOCIAL_ENGINEERING" in result["threat_types"]


def test_safe_browsing_clean_url():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}  # no "matches" key = clean
    with patch("requests.post", return_value=mock_resp):
        client = SafeBrowsingClient(api_key="test_key")
        result = client.check_url("https://google.com")
    assert result["is_threat"] is False
    assert result["threat_types"] == []


def test_safe_browsing_api_error_returns_safe():
    with patch("requests.post", side_effect=Exception("timeout")):
        client = SafeBrowsingClient(api_key="test_key")
        result = client.check_url("https://example.com")
    assert result["is_threat"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_deployment_config.py::test_safe_browsing_detects_threat -v
```

Expected: `FAILED` — current implementation always returns `is_threat: False` regardless.

- [ ] **Step 3: Replace mock implementation in `src/external/safe_browsing.py`**

Replace the entire file content:

```python
import requests
from typing import Dict, Any, List
from src.core.config import settings
from src.core.logger import log

SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

THREAT_TYPES = [
    "MALWARE",
    "SOCIAL_ENGINEERING",
    "UNWANTED_SOFTWARE",
    "POTENTIALLY_HARMFUL_APPLICATION",
]


class SafeBrowsingClient:
    """Google Safe Browsing API v4 integration."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.SAFE_BROWSING_API_KEY

    def check_url(self, url: str) -> Dict[str, Any]:
        """
        Check if a URL is flagged by Google Safe Browsing.

        Returns dict with keys:
          - is_threat (bool)
          - threat_types (list of str)
          - platform_type (str)
          - threat_entry_type (str)
        """
        log.info(f"Checking Google Safe Browsing for: {url}")

        try:
            payload = {
                "client": {
                    "clientId": "tgis-phishing-detector",
                    "clientVersion": "1.0.0",
                },
                "threatInfo": {
                    "threatTypes": THREAT_TYPES,
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}],
                },
            }
            response = requests.post(
                f"{SAFE_BROWSING_ENDPOINT}?key={self.api_key}",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            matches = data.get("matches", [])
            threat_types = [m.get("threatType", "") for m in matches]

            return {
                "is_threat": len(matches) > 0,
                "threat_types": threat_types,
                "platform_type": "ANY_PLATFORM",
                "threat_entry_type": "URL",
            }

        except Exception as e:
            log.warning(f"Safe Browsing check failed for {url}: {e}. Defaulting to safe.")
            return {
                "is_threat": False,
                "threat_types": [],
                "platform_type": "ANY_PLATFORM",
                "threat_entry_type": "URL",
            }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_deployment_config.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add src/external/safe_browsing.py tests/test_deployment_config.py
git commit -m "feat: wire real Google Safe Browsing API v4"
```

---

## Task 4: Fix Dashboard API Client URL

**Files:**
- Modify: `dashboard/utils/api_client.py`
- Test: `tests/test_deployment_config.py` (extend)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_deployment_config.py`:

```python
def test_api_client_reads_env_url(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://tgis-api.fly.dev")
    import importlib
    import dashboard.utils.api_client as mod
    importlib.reload(mod)
    client = mod.APIClient()
    assert client.base_url == "https://tgis-api.fly.dev"


def test_api_client_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    import importlib
    import dashboard.utils.api_client as mod
    importlib.reload(mod)
    client = mod.APIClient()
    assert client.base_url == "http://localhost:8000"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_deployment_config.py::test_api_client_reads_env_url -v
```

Expected: `FAILED` — client ignores env var, always uses `localhost:8000`.

- [ ] **Step 3: Update `dashboard/utils/api_client.py`**

Replace the entire file:

```python
import os
import requests
from typing import Dict, Any

_DEFAULT_BASE_URL = "http://localhost:8000"


class APIClient:
    """Helper client for communicating with the FastAPI backend."""

    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")

    def predict_url(self, url: str) -> Dict[str, Any]:
        """Request a single URL prediction from the backend."""
        try:
            payload = {
                "url": url,
                "include_explanation": True,
                "fetch_content": True,
            }
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=payload,
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"API Error ({response.status_code}): {response.text}"}
        except Exception as e:
            return {"error": f"Connection Failed: {str(e)}"}

    def get_health(self) -> Dict[str, Any]:
        """Fetch system health status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {"status": "error"}
        except Exception:
            return {"status": "offline"}
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
pytest tests/test_deployment_config.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add dashboard/utils/api_client.py tests/test_deployment_config.py
git commit -m "feat: read API_BASE_URL from env in dashboard client"
```

---

## Task 5: Create `.dockerignore`

**Files:**
- Create: `.dockerignore`

No tests needed — this only affects Docker build context size.

- [ ] **Step 1: Create `.dockerignore` at project root**

```
# Python
__pycache__/
*.py[cod]
*.pyo

# Environment & secrets
.env
.env.*

# Logs
logs/
*.log

# Dev artifacts
.git/
.gitignore
test_out*.txt
build_out.txt
pytest_*.txt
pytest.ini

# Docs
docs/
*.md

# Tests (not needed at runtime)
tests/
scripts/test_*.py
test_safe_browsing.py

# IDE
.vscode/
.idea/
```

- [ ] **Step 2: Commit**

```bash
git add .dockerignore
git commit -m "chore: add .dockerignore to keep images lean"
```

---

## Task 6: Create `Dockerfile.api`

**Files:**
- Create: `Dockerfile.api`

- [ ] **Step 1: Create `Dockerfile.api` at project root**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY api/ api/
COPY src/ src/
COPY data/ data/
COPY .env.example .env.example

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Build locally to verify it compiles**

```bash
docker build -f Dockerfile.api -t tgis-api-local .
```

Expected: `Successfully built <image_id>` with no errors.

- [ ] **Step 3: Run locally to verify it starts**

```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://phishing_user:secure_password@host.docker.internal:5432/phishing_db" \
  -e SAFE_BROWSING_API_KEY="your_key_here" \
  -e SECRET_KEY="test_secret" \
  tgis-api-local
```

Expected: `Application startup complete.` in logs. Visit `http://localhost:8000/health` and get `{"status":"healthy"}`.

- [ ] **Step 4: Stop the container and commit**

```bash
git add Dockerfile.api
git commit -m "feat: add Dockerfile for FastAPI backend"
```

---

## Task 7: Create `Dockerfile.dashboard`

**Files:**
- Create: `Dockerfile.dashboard`

- [ ] **Step 1: Create `Dockerfile.dashboard` at project root**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY dashboard/ dashboard/
COPY src/ src/
COPY data/ data/

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

- [ ] **Step 2: Build locally to verify it compiles**

```bash
docker build -f Dockerfile.dashboard -t tgis-dashboard-local .
```

Expected: `Successfully built <image_id>` with no errors.

- [ ] **Step 3: Run locally to verify it starts**

```bash
docker run --rm -p 8501:8501 \
  -e API_BASE_URL="http://host.docker.internal:8000" \
  tgis-dashboard-local
```

Expected: Streamlit starts and `http://localhost:8501` loads the dashboard.

- [ ] **Step 4: Stop the container and commit**

```bash
git add Dockerfile.dashboard
git commit -m "feat: add Dockerfile for Streamlit dashboard"
```

---

## Task 8: Create `fly.api.toml`

**Files:**
- Create: `fly.api.toml`

- [ ] **Step 1: Create `fly.api.toml` at project root**

```toml
app = "tgis-api"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile.api"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    path = "/health"
    timeout = "5s"

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

- [ ] **Step 2: Commit**

```bash
git add fly.api.toml
git commit -m "feat: add Fly.io config for API service"
```

---

## Task 9: Create `fly.dashboard.toml`

**Files:**
- Create: `fly.dashboard.toml`

- [ ] **Step 1: Create `fly.dashboard.toml` at project root**

```toml
app = "tgis-dashboard"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile.dashboard"

[http_service]
  internal_port = 8501
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1
```

- [ ] **Step 2: Commit**

```bash
git add fly.dashboard.toml
git commit -m "feat: add Fly.io config for dashboard service"
```

---

## Task 10: Update `.env.example`

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Replace `.env.example` with the full production-aware version**

```bash
# API Configuration
PORT=8000
HOST=0.0.0.0
DEBUG=False

# External API Keys
SAFE_BROWSING_API_KEY=your_google_safe_browsing_api_key

# Database (use Neon connection string in production)
DATABASE_URL=postgresql://phishing_user:secure_password@localhost:5432/phishing_db

# Redis (optional — system falls back gracefully if unavailable)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Model paths
MODEL_PATH=data/models/
LOG_LEVEL=INFO

# Security
SECRET_KEY=your_secret_key_minimum_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS — set to your Streamlit URL in production
ALLOWED_ORIGIN=http://localhost:8501

# Dashboard — set to your API URL in production
API_BASE_URL=http://localhost:8000
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: update .env.example with production vars"
```

---

## Task 11: Neon Account + Database Setup

This is a one-time manual setup. No code changes.

- [ ] **Step 1: Create a Neon account**

Go to https://neon.tech and sign up (free, no credit card needed).

- [ ] **Step 2: Create a new project**

- Click "New Project"
- Name: `tgis-phishing`
- Region: `US East (N. Virginia)` — matches Fly.io `iad` region for lowest latency
- Click "Create Project"

- [ ] **Step 3: Copy the connection string**

On the project dashboard, click "Connection Details". Select:
- Role: `neondb_owner`
- Database: `neondb`
- Connection string format: `Connection string`

Copy the string — it looks like:
```
postgresql://neondb_owner:xxxx@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

Save this — it becomes `DATABASE_URL` in Fly.io secrets.

- [ ] **Step 4: Verify connection locally (optional)**

Replace your local `.env` `DATABASE_URL` temporarily and restart the API:
```bash
uvicorn api.main:app --reload --port 8000
```
Expected: `✅ Database schema synchronized successfully.` — Neon creates the tables automatically.

---

## Task 12: Fly.io Account Setup + Deploy

- [ ] **Step 1: Create a Fly.io account**

Go to https://fly.io and sign up. The Hobby plan is free — no credit card required for the free tier allowance.

- [ ] **Step 2: Install the Fly CLI**

**Windows (PowerShell as Admin):**
```powershell
winget install flyctl
```

**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

Verify:
```bash
fly version
```
Expected: `fly v0.x.x ...`

- [ ] **Step 3: Log in**

```bash
fly auth login
```

This opens a browser window. Complete login, then return to terminal.

- [ ] **Step 4: Reserve the two app names**

```bash
fly apps create tgis-api
fly apps create tgis-dashboard
```

Expected: `New app created: tgis-api` and `New app created: tgis-dashboard`.

> If `tgis-api` is already taken by another user, choose a different name (e.g. `tgis-phishing-api`) and update `fly.api.toml` and `fly.dashboard.toml` accordingly, plus update `ALLOWED_ORIGIN` and `API_BASE_URL` secrets below.

- [ ] **Step 5: Generate a SECRET_KEY**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (64-char hex string).

- [ ] **Step 6: Set secrets for the API**

```bash
fly secrets set \
  DATABASE_URL="postgresql://neondb_owner:xxxx@ep-xxx.neon.tech/neondb?sslmode=require" \
  SAFE_BROWSING_API_KEY="AIzaSy..." \
  SECRET_KEY="<paste 64-char hex from Step 5>" \
  ALLOWED_ORIGIN="https://tgis-dashboard.fly.dev" \
  DEBUG="False" \
  --app tgis-api
```

- [ ] **Step 7: Set secrets for the dashboard**

```bash
fly secrets set \
  API_BASE_URL="https://tgis-api.fly.dev" \
  --app tgis-dashboard
```

- [ ] **Step 8: Deploy the API first**

```bash
fly deploy --config fly.api.toml
```

Expected output ends with:
```
Visit your newly deployed app at https://tgis-api.fly.dev/
```

Verify it's live:
```bash
curl https://tgis-api.fly.dev/health
```
Expected: `{"status":"healthy","version":"1.0.0",...}`

- [ ] **Step 9: Deploy the dashboard**

```bash
fly deploy --config fly.dashboard.toml
```

Expected output ends with:
```
Visit your newly deployed app at https://tgis-dashboard.fly.dev/
```

- [ ] **Step 10: Open the app**

```bash
fly open --app tgis-dashboard
```

This opens `https://tgis-dashboard.fly.dev` in your browser. Submit a URL and verify you get a prediction back.

- [ ] **Step 11: Check logs if anything looks wrong**

```bash
fly logs --app tgis-api
fly logs --app tgis-dashboard
```

---

## Post-Deploy Verification Checklist

- [ ] `https://tgis-api.fly.dev/health` returns `{"status":"healthy"}`
- [ ] `https://tgis-api.fly.dev/docs` loads the Swagger UI
- [ ] Dashboard at `https://tgis-dashboard.fly.dev` shows backend status as `ONLINE`
- [ ] Submit `https://microsoft.com` → prediction returns `SAFE`
- [ ] Submit `https://rnicrosoft.com` → prediction returns `PHISHING`
- [ ] Check `https://tgis-api.fly.dev/api/v1/history` — shows saved predictions
- [ ] Analytics tab in dashboard shows data
