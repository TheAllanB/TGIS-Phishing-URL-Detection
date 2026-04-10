"""
Quick test for the Google Safe Browsing API key.
Checks one known-safe URL and one known-phishing URL.

Run with: python test_safe_browsing.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SAFE_BROWSING_API_KEY")
ENDPOINT = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={API_KEY}"

TEST_URLS = [
    "https://google.com",           # should be clean
    "http://malware.testing.google.test/testing/malware/",  # Google's official test URL
]

def check_urls(urls: list) -> dict:
    payload = {
        "client": {
            "clientId": "tgis-phishing-detector",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url} for url in urls]
        }
    }
    response = requests.post(ENDPOINT, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    if not API_KEY or API_KEY == "your_google_safe_browsing_api_key":
        print("❌ SAFE_BROWSING_API_KEY not set in .env")
        exit(1)

    print(f"Testing {len(TEST_URLS)} URLs against Google Safe Browsing...\n")

    result = check_urls(TEST_URLS)
    matches = result.get("matches", [])

    if not matches:
        print("✅ API key works. No threats found (google.com is clean as expected).")
    else:
        for match in matches:
            print(f"⚠️  Threat detected: {match['threat']['url']}")
            print(f"   Type: {match['threatType']}, Platform: {match['platformType']}")

    print("\n✅ Safe Browsing API is working correctly.")
