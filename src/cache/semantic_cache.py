import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheResult:
    def __init__(self, cache_key: str, similarity: float, subgraph: Dict[str, Any], hit_type: str):
        self.cache_key = cache_key
        self.query_similarity = similarity
        self.cached_subgraph = subgraph
        self.hit_type = hit_type

class SemanticCache:
    """Stores and retrieves knowledge subgraphs based on semantic query similarity with multi-tenant support."""
    
    def __init__(self, similarity_threshold: float = 0.75, redis_url: str = None):
        self.similarity_threshold = similarity_threshold
        self.redis = None
        self.in_memory_store = {}
        
        try:
            if redis_url:
                import redis
                self.redis = redis.from_url(redis_url)
                self.redis.ping()
                logger.info("SemanticCache connected to Redis.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Using in-memory fallback cache.")
            self.redis = None
            
    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    def lookup(self, tenant_id: str, query_embedding: list) -> Optional[CacheResult]:
        best_match = None
        highest_sim = 0.0
        prefix = f"cache:{tenant_id}:"
        
        if self.redis:
            keys = self.redis.keys(f"{prefix}*")
            for key in keys:
                data = json.loads(self.redis.get(key))
                sim = self._cosine_similarity(query_embedding, data["embedding"])
                if sim > highest_sim:
                    highest_sim = sim
                    best_match = data
        else:
            for key, data in self.in_memory_store.items():
                if key.startswith(prefix):
                    sim = self._cosine_similarity(query_embedding, data["embedding"])
                    if sim > highest_sim:
                        highest_sim = sim
                        best_match = data
                    
        if best_match and highest_sim >= self.similarity_threshold:
            hit_type = "full" if highest_sim >= 0.95 else "partial"
            if self.redis:
                best_match["hit_count"] += 1
                best_match["last_accessed"] = datetime.utcnow().isoformat()
                self.redis.set(best_match["cache_key"], json.dumps(best_match))
                
            return CacheResult(
                cache_key=best_match["cache_key"],
                similarity=highest_sim,
                subgraph=best_match["cached_subgraph"],
                hit_type=hit_type
            )
            
        return None

    def store(self, tenant_id: str, query_id: str, query_embedding: list, result_subgraph: Dict[str, Any], ttl_hours: int = 24) -> str:
        cache_key = f"cache:{tenant_id}:{query_id}"
        entry = {
            "cache_key": cache_key,
            "embedding": query_embedding,
            "cached_subgraph": result_subgraph,
            "stored_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat(),
            "hit_count": 0,
            "last_accessed": datetime.utcnow().isoformat()
        }
        
        if self.redis:
            self.redis.setex(cache_key, ttl_hours * 3600, json.dumps(entry))
        else:
            self.in_memory_store[cache_key] = entry
            
        logger.debug(f"Stored {cache_key} in semantic cache with TTL {ttl_hours}h.")
        return cache_key
