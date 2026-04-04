import whois
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.external.cache_manager import cache_manager
from src.core.logger import log

class WHOISClient:
    """
    Client for retrieving domain registration data via WHOIS protocols.
    Features integrated Redis caching and robust data normalization.
    """
    
    CACHE_PREFIX = "whois:"
    CACHE_TTL = 604800  # 7 days in seconds

    def lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Query WHOIS information for a domain with caching.
        
        Args:
            domain (str): The domain name to look up.
            
        Returns:
            Optional[Dict[str, Any]]: Normalized WHOIS data or None if failed.
        """
        cache_key = f"{self.CACHE_PREFIX}{domain}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            return cached_data

        log.info(f"Performing WHOIS lookup for domain: {domain}")
        try:
            # Query domain metadata
            w = whois.whois(domain)
            
            if not w or not w.domain_name:
                log.warning(f"No WHOIS record found for: {domain}")
                return None
                
            # Parse and normalize result
            result = self._parse_whois(w)
            
            # Store in cache
            if result:
                cache_manager.set(cache_key, result, ttl=self.CACHE_TTL)
            
            return result
        except Exception as e:
            log.error(f"WHOIS lookup failed for {domain}: {e}")
            return None

    def _parse_whois(self, w: Any) -> Dict[str, Any]:
        """
        Normalize the python-whois output.
        Handles cases where fields can be either string or list of strings.
        """
        def first_or_val(val):
            if isinstance(val, list) and len(val) > 0:
                return val[0]
            return val

        # Handle dates (can be list or single datetime)
        def parse_date(date_val):
            if isinstance(date_val, list):
                date_val = date_val[0]
            if isinstance(date_val, datetime):
                return date_val.isoformat()
            return str(date_val) if date_val else None

        return {
            "domain_name": first_or_val(w.domain_name).lower() if w.domain_name else None,
            "creation_date": parse_date(w.creation_date),
            "expiration_date": parse_date(w.expiration_date),
            "updated_date": parse_date(w.updated_date),
            "registrar": first_or_val(w.registrar),
            "registrant_country": first_or_val(w.country),
            "name_servers": [ns.lower() for ns in w.name_servers] if w.name_servers else [],
            "status": w.status if isinstance(w.status, list) else [w.status] if w.status else [],
            "dnssec": first_or_val(w.dnssec)
        }
