# Deployment Design — TGIS Phishing URL Detection
**Date:** 2026-04-10  
**Status:** Approved  
**Platform:** Fly.io (compute) + Neon (PostgreSQL)  
**Target cost:** $0/month (free tier)

---

## 1. Project Specs

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn (Python 3.12) |
| Frontend | Streamlit |
| Database | PostgreSQL via SQLAlchemy + psycopg2 |
| Cache | Redis (optional — graceful fallback, skipped in production) |
| ML Models | Random Forest (352KB) + XGBoost (216KB) + imputer/scaler (8KB) |
| Trust Graph | NetworkX .gpickle (8.6KB) |
| External APIs | Google Safe Browsing (real), WHOIS, DNS, SSL |
| Total model assets | ~600KB — deployed alongside code, no object storage needed |

**Is a database required in production?** Yes. PostgreSQL stores prediction history and feature vectors, powering the analytics dashboard tab. The app degrades gracefully if the DB is unavailable, but history/analytics will be empty.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Fly.io Cloud                         │
│                                                             │
│  ┌──────────────────────┐    ┌──────────────────────────┐  │
│  │  tgis-dashboard      │───▶│  tgis-api                │  │
│  │  Streamlit           │    │  FastAPI + Uvicorn        │  │
│  │  tgis-dashboard.     │    │  tgis-api.fly.dev         │  │
│  │  fly.dev             │    │  min_machines_running = 1 │  │
│  │  min_machines_running│    │  port 8000                │  │
│  │  = 1, port 8501      │    └──────────┬───────────────┘  │
│  └──────────────────────┘               │                   │
│                                         │ DATABASE_URL       │
└─────────────────────────────────────────┼───────────────────┘
                                          ▼
                              ┌───────────────────────┐
                              │  Neon (Serverless PG)  │
                              │  predictions table     │
                              │  feature_vectors table │
                              │  Free tier: 0.5GB      │
                              └───────────────────────┘
```

**Two always-on Fly.io machines.** `min_machines_running = 1` prevents cold starts on the free tier. The dashboard calls the API via its public `fly.dev` URL (not localhost). Redis is omitted — the CacheManager already falls back to no-op when unavailable.

---

## 3. Public URLs

| Service | URL |
|---|---|
| Dashboard (user-facing) | `https://tgis-dashboard.fly.dev` |
| API | `https://tgis-api.fly.dev` |
| API docs (Swagger) | `https://tgis-api.fly.dev/docs` |

App names (`tgis-api`, `tgis-dashboard`) are chosen at `fly apps create` time — pick anything not already taken on Fly.io. Custom domains can be pointed via CNAME at no extra cost.

---

## 4. Code Changes Required

### 4a. `dashboard/utils/api_client.py`
Change the hardcoded `http://localhost:8000` base URL to read from the `API_BASE_URL` environment variable, falling back to localhost for local development.

### 4b. `src/external/safe_browsing.py`
Replace the mock implementation with a real HTTP POST to `https://safebrowsing.googleapis.com/v4/threatMatches:find`, using the `SAFE_BROWSING_API_KEY` from settings.

### 4c. `api/main.py` — CORS
Tighten `allow_origins=["*"]` to `["https://tgis-dashboard.fly.dev"]` in production. Use an env var `ALLOWED_ORIGIN` so localhost still works in dev.

### 4d. `Dockerfile.api`
Multi-stage Python image. Copies source, installs `requirements.txt`, runs `uvicorn api.main:app --host 0.0.0.0 --port 8000`.

### 4e. `Dockerfile.dashboard`
Python image. Copies source, installs `requirements.txt`, runs `streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0`.

### 4f. `fly.api.toml`
Fly.io config for the API service: app name, port 8000, `min_machines_running = 1`, health check on `/health`.

### 4g. `fly.dashboard.toml`
Fly.io config for the dashboard: app name, port 8501, `min_machines_running = 1`.

---

## 5. Environment Variables

### API service (`tgis-api`)
| Variable | Source |
|---|---|
| `DATABASE_URL` | Neon dashboard connection string |
| `SAFE_BROWSING_API_KEY` | Google Cloud Console |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ALLOWED_ORIGIN` | `https://tgis-dashboard.fly.dev` |
| `DEBUG` | `False` |

### Dashboard service (`tgis-dashboard`)
| Variable | Source |
|---|---|
| `API_BASE_URL` | `https://tgis-api.fly.dev` |

---

## 6. Deployment Steps

### Prerequisites (one-time)
1. Create account at [fly.io](https://fly.io)
2. Install Fly CLI: `winget install flyctl` (Windows) or `curl -L https://fly.io/install.sh | sh`
3. Create account at [neon.tech](https://neon.tech), create a project, copy the `DATABASE_URL`

### Deploy
```bash
# 1. Login
fly auth login

# 2. Create the two apps (reserves the .fly.dev subdomains)
fly apps create tgis-api
fly apps create tgis-dashboard

# 3. Set secrets for the API
fly secrets set \
  DATABASE_URL="postgresql://..." \
  SAFE_BROWSING_API_KEY="AIza..." \
  SECRET_KEY="<generated>" \
  ALLOWED_ORIGIN="https://tgis-dashboard.fly.dev" \
  DEBUG="False" \
  --app tgis-api

# 4. Set secrets for the dashboard
fly secrets set \
  API_BASE_URL="https://tgis-api.fly.dev" \
  --app tgis-dashboard

# 5. Deploy API first (dashboard depends on it)
fly deploy --config fly.api.toml

# 6. Deploy dashboard
fly deploy --config fly.dashboard.toml
```

### Verify
```bash
fly logs --app tgis-api
fly logs --app tgis-dashboard
fly open --app tgis-dashboard
```

---

## 7. What Is NOT Changing

- No changes to ML models, training pipeline, feature extractors, or graph logic
- No changes to database schema or ORM models
- No changes to API route signatures or response schemas
- Redis remains optional with graceful fallback (no Redis in production)
- All model files ship inside the Docker image (they are tiny at ~600KB total)
