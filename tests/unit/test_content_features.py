import unittest
from unittest.mock import Mock, patch
from src.features.content_features import ContentFeatureExtractor

class TestContentFeatureExtractor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = ContentFeatureExtractor(timeout=1)

    @patch('requests.get')
    def test_successful_html_extraction(self, mock_get):
        # Mock HTML content with specific phishing signals
        html = """
        <html>
            <head><title>Login to PayPal</title></head>
            <body>
                <form action="/login" method="POST">
                    <input type="password" name="pass">
                </form>
                <iframe src="http://evil.com"></iframe>
                <a href="https://legit.com">Internal</a>
                <a href="http://external.com">External</a>
                <script>eval(atob('YWxlcnQoMSk=')); window.open('popup');</script>
                <img src="http://insecure.com/img.png">
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.text = html
        mock_response.url = "https://safe-pay-pal.com/verify"
        mock_response.history = [Mock(), Mock()] # Simulate 2 redirects
        mock_get.return_value = mock_response
        
        features = self.extractor.extract("https://safe-pay-pal.com/verify")
        
        # Verification
        assert features['has_login_form'] == 1
        assert features['form_has_password_field'] == 1
        assert features['has_iframe'] == 1
        assert features['num_external_links'] == 1
        assert features['num_internal_links'] == 2 # 1 <a> + 1 <link/src>
        assert features['num_redirects'] == 2
        assert features['has_popup'] == 1
        assert features['uses_javascript_obfuscation'] == 1
        assert features['html_title_brand_mismatch'] == 1 # "PayPal" in title, not in domain
        assert features['has_mixed_content'] == 1 # HTTP img in HTTPS page

    @patch('requests.get')
    def test_unreachable_page_defaults(self, mock_get):
        # Mock connection error/timeout
        mock_get.side_effect = Exception("Connection Timeout")
        
        features = self.extractor.extract("https://blackhole.com")
        
        # Verification: all features should be -1
        assert features['has_login_form'] == -1
        assert features['num_external_links'] == -1
        assert features['num_internal_links'] == -1
        assert features['uses_https'] == -1

    def test_architectural_count(self):
        features = self.extractor._get_default_features()
        assert len(features) == 15
