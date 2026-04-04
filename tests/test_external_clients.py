import time
from src.external.cache_manager import cache_manager
from src.external.whois_client import WHOISClient
from src.external.dns_resolver import DNSResolver
from src.external.ssl_checker import SSLChecker
from src.core.logger import log

def verify_external_clients():
    domain = "google.com"
    
    whois_client = WHOISClient()
    dns_resolver = DNSResolver()
    ssl_checker = SSLChecker()
    
    log.info(f"--- 🚀 STAGE 1: External Query Verification ({domain}) ---")
    
    # 1. WHOIS
    log.info("Testing WHOIS Client...")
    whois_start = time.time()
    whois_data = whois_client.lookup(domain)
    log.info(f"WHOIS Response (Time: {time.time()-whois_start:.2f}s):")
    if whois_data:
        log.success(f"Registrar: {whois_data.get('registrar')}")
        log.info(f"Creation Date: {whois_data.get('creation_date')}")
    else:
        log.error("WHOIS Lookup Failed.")

    # 2. DNS
    log.info("Testing DNS Resolver...")
    dns_start = time.time()
    dns_data = dns_resolver.resolve(domain)
    log.info(f"DNS Response (Time: {time.time()-dns_start:.2f}s):")
    if dns_data:
        log.success(f"A Records: {dns_data.get('A_records')}")
        log.info(f"Record Count: {dns_data.get('dns_record_count')}")
    else:
        log.error("DNS Resolution Failed.")

    # 3. SSL
    log.info("Testing SSL Checker...")
    ssl_start = time.time()
    ssl_data = ssl_checker.check(domain)
    log.info(f"SSL Response (Time: {time.time()-ssl_start:.2f}s):")
    if ssl_data:
        log.success(f"Issuer: {ssl_data.get('issuer')}")
        log.info(f"Valid Until: {ssl_data.get('not_after')}")
    else:
        log.error("SSL Check Failed.")

    log.info(f"--- ♻️ STAGE 2: Cache Verification ({domain}) ---")
    
    # Repeat WHOIS to verify cache hit
    log.info("Repeating WHOIS lookup to verify cache hit...")
    cache_start = time.time()
    whois_client.lookup(domain)
    cache_duration = time.time() - cache_start
    
    if cache_duration < 0.1:  # Cache hit should be near instant
        log.success(f"Cache Hit confirmed (Duration: {cache_duration*1000:.2f}ms)")
    else:
        log.warning(f"Cache Hit not detected OR slow Redis (Duration: {cache_duration*1000:.2f}ms)")

if __name__ == "__main__":
    verify_external_clients()
