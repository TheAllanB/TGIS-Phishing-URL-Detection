import ssl
import socket
from datetime import datetime
from typing import Optional, Dict, Any
from src.external.cache_manager import cache_manager
from src.core.logger import log

class SSLChecker:
    """
    SSL certificate validation and metadata extraction using standard Python libraries.
    Captures issuer details, validity dates, and certificate status.
    """
    
    CACHE_PREFIX = "ssl:"
    CACHE_TTL = 86400  # 24 hours in seconds

    def check(self, domain: str, port: int = 443) -> Optional[Dict[str, Any]]:
        """
        Extract SSL certificate details for a domain with caching.
        
        Args:
            domain (str): The domain to check.
            port (int): The HTTPS port (default: 443).
            
        Returns:
            Optional[Dict[str, Any]]: Normalized SSL certificate metadata.
        """
        cache_key = f"{self.CACHE_PREFIX}{domain}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            return cached_data

        log.info(f"Checking SSL certificate for domain: {domain}")
        result = {}
        
        try:
            # Setup context and establish connection
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if not cert:
                        log.warning(f"No SSL certificate returned for: {domain}")
                        return {"is_valid": False}
                        
                    # Parse certificate details
                    result = self._parse_cert(cert)
                    result["is_valid"] = True
                    result["is_trusted"] = True  # If handshake succeeded with default context
                    
            # Store in cache
            if result:
                cache_manager.set(cache_key, result, ttl=self.CACHE_TTL)
            
            return result
        except ssl.SSLError as e:
            log.warning(f"SSL handshake failed for {domain}: {e}")
            return {"is_valid": False, "is_trusted": False, "error": str(e)}
        except (socket.timeout, socket.error, Exception) as e:
            log.error(f"Network error checking SSL for {domain}: {e}")
            return None

    def _parse_cert(self, cert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helpers to normalize SSL certificate dictionary fields.
        """
        def parse_date(date_str: str) -> Optional[str]:
            try:
                # SSL date format: "Mar 11 23:59:59 2024 GMT"
                dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                return dt.isoformat()
            except Exception:
                return date_str

        # Flatten issuer and subject lists
        # Example: ((('commonName', 'google.com'),),) -> 'google.com'
        def flatten_rdns(rdns) -> str:
            parts = []
            for rdn in rdns:
                for entry in rdn:
                    parts.append(f"{entry[0]}={entry[1]}")
            return ", ".join(parts)

        return {
            "issuer": flatten_rdns(cert.get('issuer', [])),
            "subject": flatten_rdns(cert.get('subject', [])),
            "not_before": parse_date(cert.get('notBefore')),
            "not_after": parse_date(cert.get('notAfter')),
            "serial_number": cert.get('serialNumber'),
            "version": cert.get('version'),
            "ocsp_endpoints": cert.get('OCSP', []),
            "ca_issuers": cert.get('caIssuers', [])
        }
