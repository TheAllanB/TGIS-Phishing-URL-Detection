import json
import redis
from typing import Optional, Any
from src.core.config import settings
from src.core.logger import log

class CacheManager:
    """
    Redis-based caching system for external API responses and computed features.
    Provides a centralized interface with JSON serialization and expiration support.
    """
    
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Basic connectivity test
            self.client.ping()
            self.enabled = True
            log.info(f"Redis Cache initialized at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            log.warning(f"Redis Cache unavailable: {e}. Falling back to no-cache mode.")
            self.enabled = False
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache by key.
        
        Args:
            key (str): The cache key.
            
        Returns:
            Optional[dict]: Deserialized data if found, else None.
        """
        if not self.enabled or not self.client:
            return None
            
        try:
            data = self.client.get(key)
            if data:
                log.debug(f"Cache HIT for key: {key}")
                return json.loads(data)
            log.debug(f"Cache MISS for key: {key}")
            return None
        except Exception as e:
            log.error(f"Error retrieving from cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Store data in cache with an expiration time.
        
        Args:
            key (str): The cache key.
            value (Any): Data to be stored (must be JSON-serializable).
            ttl (int): Time-to-live in seconds (default: 1 hour).
            
        Returns:
            bool: True if successful, else False.
        """
        if not self.enabled or not self.client:
            return False
            
        try:
            serialized_value = json.dumps(value, default=str)
            self.client.set(key, serialized_value, ex=ttl)
            log.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            log.error(f"Error storing in cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.
        """
        if not self.enabled or not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            log.error(f"Error deleting from cache: {e}")
            return False

# Global CacheManager instance
cache_manager = CacheManager()
