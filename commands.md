# Commands Reference

## Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Copy the example env file and fill in your values
cp .env.example .env
```

## Running Locally

Open two terminals and run one command in each:

```bash
# Terminal 1 — Backend API (http://localhost:8000)
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend Dashboard (http://localhost:8501)
streamlit run dashboard/app.py
```

API docs are available at: http://localhost:8000/docs

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov=api

# Run a specific test file
pytest tests/test_prediction_service.py -v
```

## Database

```bash
# The database schema is created automatically on API startup.
# To connect manually via psql:
psql $DATABASE_URL

# To reset the schema (drops and recreates all tables):
python -c "from api.database import engine, Base; import api.models; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

## Training

```bash
# Retrain models from scratch (outputs to data/models/)
python src/train.py
```

## Deployment (Fly.io)

```bash
# Install Fly CLI (run once)
# Windows:  https://fly.io/install.ps1
# Mac/Linux: curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy the API
fly deploy --config fly.api.toml

# Deploy the dashboard
fly deploy --config fly.dashboard.toml

# View live logs
fly logs --config fly.api.toml
fly logs --config fly.dashboard.toml

# Open the deployed app in browser
fly open --config fly.dashboard.toml

# Set a secret environment variable
fly secrets set VARIABLE_NAME=value --config fly.api.toml
```
