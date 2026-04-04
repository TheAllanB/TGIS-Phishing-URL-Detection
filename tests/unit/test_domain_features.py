import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from src.features.domain_features import DomainFeatureExtractor

class TestDomainFeatureExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = DomainFeatureExtractor()
        # Mock external clients to avoid actual network calls
        self.extractor.whois_client = Mock()
        self.extractor.dns_resolver = Mock()
        self.extractor.ssl_checker = Mock()

    def test_successful_extraction(self):
        now = datetime.now()
        creation_date = (now - timedelta(days=365)).isoformat()
        expiration_date = (now + timedelta(days=365)).isoformat()
        
        # Mock WHOIS response
        self.extractor.whois_client.lookup.return_value = {
            "domain_name": "google.com",
            "creation_date": creation_date,
            "expiration_date": expiration_date,
            "registrar": "MarkMonitor Inc.",
            "country": "US"
        }
        
        # Mock DNS response
        self.extractor.dns_resolver.resolve.return_value = {
            "A_records": ["1.1.1.1"],
            "MX_records": ["mx.google.com"],
            "TXT_records": ["v=spf1 include:_spf.google.com ~all"],
            "NS_records": ["ns1.google.com", "ns2.google.com"],
            "dns_record_count": 4
        }
        
        # Mock SSL response
        self.extractor.ssl_checker.check.return_value = {
            "is_valid": True,
            "is_trusted": True,
            "not_before": (now - timedelta(days=30)).isoformat()
        }
        
        features = self.extractor.extract("https://www.google.com")
        
        # Verification
        assert features['domain_age_days'] >= 364
        assert features['domain_expiry_days'] >= 364
        assert features['is_registered'] == 1
        assert features['has_mx_record'] == 1
        assert features['has_spf_record'] == 1
        assert features['ssl_certificate_valid'] == 1
        assert features['registrar_reputation_score'] == 0.9 # MarkMonitor is top-tier
        assert features['domain_in_brand_list'] == 1 # "google" is in BRAND_LIST

    def test_failed_lookups_defaults(self):
        # Mock clients to return None or failure indicators
        self.extractor.whois_client.lookup.return_value = None
        self.extractor.dns_resolver.resolve.return_value = None
        self.extractor.ssl_checker.check.return_value = {"is_valid": False}
        
        features = self.extractor.extract("https://unknown-domain.com")
        
        # Verification: features should default to 0/False/-1 rather than crashing
        assert features['is_registered'] == 0
        assert features['domain_age_days'] == 0
        assert features['has_mx_record'] == 0
        assert features['ssl_certificate_valid'] == 0
        assert features['dns_record_count'] == 0

    def test_brand_mimicry(self):
        # Even if lookup fails, string analysis should detect brands
        self.extractor.whois_client.lookup.return_value = None
        
        features = self.extractor.extract("https://paypal-system-update.com")
        assert features['domain_in_brand_list'] == 1
        
        features = self.extractor.extract("https://random-site.com")
        assert features['domain_in_brand_list'] == 0

    def test_entropy_calculation(self):
        # Test Shannon entropy logic
        low_entropy = "aaaaa.com"
        high_entropy = "x7k2m9p1z.com"
        
        e_low = self.extractor._calculate_entropy(low_entropy)
        e_high = self.extractor._calculate_entropy(high_entropy)
        
        assert e_high > e_low

    def test_architectural_count(self):
        self.extractor.whois_client.lookup.return_value = None
        features = self.extractor.extract("https://google.com")
        assert len(features) == 20
