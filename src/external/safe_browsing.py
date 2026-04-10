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
