from abc import ABC, abstractmethod
from typing import Dict, Any

class FeatureExtractor(ABC):
    """
    Abstract Base Class for all feature extractors in the system.
    Each extractor takes a URL/data and returns a dictionary of features.
    """
    @abstractmethod
    def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract features from the provided URL.
        
        Args:
            url (str): The target URL.
            **kwargs: Optional additional data (e.g., HTML content).
            
        Returns:
            Dict[str, Any]: A flat dictionary of features (name -> value).
        """
        pass
