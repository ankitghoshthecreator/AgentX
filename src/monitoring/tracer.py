import json
import logging
import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Tracer:
    """Records system decisions and metrics for observability."""
    
    def __init__(self):
        self.traces: List[Dict[str, Any]] = []
        logger.info("Tracer initialized.")
        
    def record_event(self, query_id: str, event_type: str, details: Dict[str, Any]):
        """Record a single operational event."""
        trace = {
            "trace_id": f"TR-{len(self.traces)+1:04d}",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "query_id": query_id,
            "event_type": event_type,
            "details": details
        }
        self.traces.append(trace)
        logger.debug(f"Traced event: {event_type} for query {query_id}")

    def export_traces(self) -> str:
        """Export all traces as JSON lines string."""
        return "\n".join(json.dumps(t) for t in self.traces)
        
    def get_metrics(self) -> Dict[str, Any]:
        """Compute basic metrics from recorded traces."""
        cache_hits = sum(1 for t in self.traces if t["event_type"] == "cache_lookup" and t["details"].get("result") in ["full", "partial"])
        cache_lookups = sum(1 for t in self.traces if t["event_type"] == "cache_lookup")
        
        return {
            "total_queries": len(set(t["query_id"] for t in self.traces)),
            "cache_hit_rate": (cache_hits / cache_lookups) if cache_lookups > 0 else 0,
            "total_events_logged": len(self.traces)
        }
