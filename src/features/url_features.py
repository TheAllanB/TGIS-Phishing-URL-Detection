import re
from urllib.parse import urlparse
from typing import Dict, Any
from src.features.base import FeatureExtractor
from src.core.logger import log

class URLFeatureExtractor(FeatureExtractor):
    """
    Extracts structural features from a URL string itself.
    These features represent the 15 categories specified in the architecture.
    """
    
    def __init__(self):
        # Special character set defined in ARCHITECTURE.md
        self.special_chars = "!@#$%^&*()+=[]{}|;:,<>?"
        
        # IP Address regular expression (IPv4 and partial IPv6 support)
        self.ip_pattern = re.compile(
            r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
            r'([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])|'
            r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|'
            r'([0-9a-fA-F]{1,4}:){1,7}:|'
            r'([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|'
            r'([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|'
            r'([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|'
            r'([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|'
            r'([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|'
            r'[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|'
            r':((:[0-9a-fA-F]{1,4}){1,7}|:)|'
            r'fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|'
            r'::(ffff(:0{1,4}){0,1}:){0,1}'
            r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}'
            r'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|'
            r'([0-9a-fA-F]{1,4}:){1,4}:'
            r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}'
            r'(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
        )

    def extract(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Extract the 15 architectural URL features.
        
        Args:
            url (str): The URL to analyze.
            **kwargs: Not used for URL extractor.
            
        Returns:
            Dict[str, Any]: 15 key structural features.
        """
        log.debug(f"Extracting URL features for: {url}")
        
        parsed = urlparse(url)
        netloc = parsed.netloc
        path = parsed.path
        
        features = {}
        
        # 1. url_length
        features['url_length'] = len(url)
        
        # 2. domain_length
        features['domain_length'] = len(netloc)
        
        # 3. path_length
        features['path_length'] = len(path)
        
        # 4. num_dots
        features['num_dots'] = url.count('.')
        
        # 5. num_hyphens
        features['num_hyphens'] = url.count('-')
        
        # 6. num_underscores
        features['num_underscores'] = url.count('_')
        
        # 7. num_slashes
        features['num_slashes'] = url.count('/')
        
        # 8. num_question_marks
        features['num_question_marks'] = url.count('?')
        
        # 9. num_equals
        features['num_equals'] = url.count('=')
        
        # 10. num_at_symbols
        features['num_at_symbols'] = url.count('@')
        
        # 11. num_ampersands
        features['num_ampersands'] = url.count('&')
        
        # 12. num_special_chars (total count)
        features['num_special_chars'] = sum(1 for char in url if char in self.special_chars)
        
        # 13. has_ip_address
        # Extract host without port
        host = netloc.split(':')[0]
        features['has_ip_address'] = 1 if self.ip_pattern.match(host) else 0
        
        # 14. has_port
        features['has_port'] = 1 if ':' in netloc else 0
        
        # 15. subdomain_count
        # Split netloc, excluding TLD and main domain
        # Example: dev.example.com -> ['dev', 'example', 'com'] -> subdomains: ['dev']
        parts = host.split('.')
        # Standard domains have at least 2 parts (example.com)
        # Anything more is a subdomain
        features['subdomain_count'] = max(0, len(parts) - 2) if features['has_ip_address'] == 0 else 0
        
        log.debug(f"Extracted {len(features)} URL features.")
        return features
