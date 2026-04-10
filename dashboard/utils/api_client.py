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
