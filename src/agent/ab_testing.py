import logging
import random
from typing import Dict, List

logger = logging.getLogger(__name__)

class ABTestingFramework:
    """A/B Testing Framework for evaluating Tool Selection ML Policies."""
    
    def __init__(self):
        self.experiments = {
            "tool_selection_policy": ["v1.0-heuristic", "v2.0-ml-predicted"]
        }
        logger.info("A/B Testing Framework initialized.")

    def get_variant(self, query_id: str, experiment_name: str) -> str:
        """Deterministically assign a query to an A/B test variant."""
        if experiment_name not in self.experiments:
            logger.warning(f"Experiment {experiment_name} not found.")
            return "default"
            
        variants = self.experiments[experiment_name]
        # Deterministic assignment based on query_id
        assigned_variant = variants[hash(query_id) % len(variants)]
        
        logger.debug(f"Query {query_id} assigned to variant: {assigned_variant} for {experiment_name}")
        return assigned_variant
