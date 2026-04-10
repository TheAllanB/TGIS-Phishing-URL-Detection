import pytest
from src.core.config import Settings


def test_allowed_origin_defaults_to_localhost():
    s = Settings()
    assert s.ALLOWED_ORIGIN == "http://localhost:8501"


def test_allowed_origin_reads_from_env(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://tgis-dashboard.fly.dev")
    s = Settings()
    assert s.ALLOWED_ORIGIN == "https://tgis-dashboard.fly.dev"


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
    mock_resp.json.return_value = {}
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


def test_cors_does_not_use_wildcard():
    """After fix, CORS must not use wildcard * — only specific allowed origins."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.com"}
    )
    allow = response.headers.get("access-control-allow-origin", "")
    assert allow != "*", "CORS must not use wildcard * in production"
