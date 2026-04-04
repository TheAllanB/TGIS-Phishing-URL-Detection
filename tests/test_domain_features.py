from src.features.domain_features import DomainFeatureExtractor
from src.core.logger import log

def verify_domain_features():
    extractor = DomainFeatureExtractor()
    
    test_urls = [
        "https://www.google.com",
        "https://secure-login-update.facebook.account-verification.tk/login"
    ]
    
    log.info("Starting Domain Metadata and String analysis verification...")
    
    for url in test_urls:
        log.info(f"--- 🚀 Analyzing: {url} ---")
        features = extractor.extract(url)
        
        # Header
        print(f"{'Feature':<20} | {'Value':<15}")
        print("-" * 38)
        
        # Features
        for name, value in sorted(features.items()):
            print(f"{name:<20} | {value:<15}")
        print("\n")

if __name__ == "__main__":
    verify_domain_features()
