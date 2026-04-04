from typing import Dict, Any
from src.features.url_features import URLFeatureExtractor
from src.features.domain_features import DomainFeatureExtractor
from src.features.content_features import ContentFeatureExtractor
from src.core.logger import log

class FeaturePipeline:
    """
    Orchestrates the complete feature extraction process for a given URL.
    Aggregates structural, metadata, and content-based features into a single vector.
    """
    
    def __init__(self):
        log.info("Initializing Feature Engineering Pipeline...")
        self.url_extractor = URLFeatureExtractor()
        self.domain_extractor = DomainFeatureExtractor()
        self.content_extractor = ContentFeatureExtractor()

    def extract_all(self, url: str) -> Dict[str, Any]:
        """
        Execute all active extractors and merge results.
        
        Args:
            url (str): The target URL.
            
        Returns:
            Dict[str, Any]: A unified dictionary containing all 50 features.
        """
        log.info(f"--- 🌀 Pipeline Execution Started: {url} ---")
        
        # 1. URL Structural Features (15)
        url_features = self.url_extractor.extract(url)
        
        # 2. Domain Metadata Features (20)
        domain_features = self.domain_extractor.extract(url)
        
        # 3. Content-based Features (15)
        content_features = self.content_extractor.extract(url)
        
        # Merge all dictionaries
        all_features = {**url_features, **domain_features, **content_features}
        
        log.info(f"--- ✅ Pipeline Execution Completed. Total Features: {len(all_features)} ---")
        
        return all_features
