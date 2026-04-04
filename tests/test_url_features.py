from src.features.url_features import URLFeatureExtractor
from src.core.logger import log

def verify_url_features():
    extractor = URLFeatureExtractor()
    
    test_urls = [
        "https://www.google.com",
        "http://127.0.0.1:8080/login",
        "https://security-update-verification.account-protection.com/validate?user=@admin&token=123_456#home",
        "https://sub.sub2.sub3.example.co.uk/path/to/resource?q=search",
        "http://phish-site.net/webscr?cmd=_login-run&dispatch=5885d80a13c0db1f8e263663d3faee8d66f314291"
    ]
    
    log.info("Starting structural URL feature verification...")
    
    for url in test_urls:
        log.info(f"--- Analyzing: {url} ---")
        features = extractor.extract(url)
        
        # Header
        print(f"{'Feature':<20} | {'Value':<10}")
        print("-" * 35)
        
        # Features
        for name, value in features.items():
            print(f"{name:<20} | {value:<10}")
        print("\n")

if __name__ == "__main__":
    verify_url_features()
