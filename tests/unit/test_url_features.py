import pytest
from src.features.url_features import URLFeatureExtractor

@pytest.fixture
def extractor():
    return URLFeatureExtractor()

def test_url_length(extractor):
    url = "https://google.com"
    features = extractor.extract(url)
    assert features['url_length'] == len(url)

def test_subdomain_count(extractor):
    # Single subdomain: www
    assert extractor.extract("https://www.google.com")['subdomain_count'] == 1
    # Multiple subdomains: dev.static.corp
    assert extractor.extract("https://dev.static.corp.company.com")['subdomain_count'] == 3
    # No subdomain: example.com
    assert extractor.extract("https://example.com")['subdomain_count'] == 0

def test_ip_detection(extractor):
    # IPv4
    assert extractor.extract("http://192.168.1.1/login")['has_ip_address'] == 1
    # Regular domain
    assert extractor.extract("https://google.com")['has_ip_address'] == 0

def test_special_characters(extractor):
    url = "https://secure-login.com/redirect?user=@admin&token=123_456"
    features = extractor.extract(url)
    # Includes: ? (1), = (2), @ (1), & (1), _ (1)
    # Total special from architecture set "!@#$%^&*()+=[]{}|;:,<>?"
    # ?:1, =:2, @:1, &:1 -> 5
    assert features['num_question_marks'] == 1
    assert features['num_equals'] == 2
    assert features['num_at_symbols'] == 1
    assert features['num_ampersands'] == 1
    assert features['num_special_chars'] >= 5

def test_port_detection(extractor):
    assert extractor.extract("http://localhost:8000")['has_port'] == 1
    assert extractor.extract("https://google.com")['has_port'] == 0

def test_architectural_count(extractor):
    features = extractor.extract("https://google.com")
    assert len(features) == 15
