import networkx as nx
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GraphBuilder:
    """Builds and updates the semantic knowledge graph with multi-tenant support (Phase 3)."""
    
    def __init__(self):
        self.graphs: Dict[str, nx.DiGraph] = {}
        logger.info("GraphBuilder initialized with multi-tenant support.")
        
    def _get_graph(self, tenant_id: str) -> nx.DiGraph:
        if tenant_id not in self.graphs:
            self.graphs[tenant_id] = nx.DiGraph()
            logger.info(f"Initialized new knowledge graph for tenant: {tenant_id}")
        return self.graphs[tenant_id]
        
    def add_node(self, tenant_id: str, node_id: str, properties: Dict[str, Any]):
        graph = self._get_graph(tenant_id)
        graph.add_node(node_id, **properties)
        logger.debug(f"Added node {node_id} for tenant {tenant_id}")

    def add_edge(self, tenant_id: str, src: str, dst: str, relationship_type: str, metadata: Dict[str, Any]) -> bool:
        graph = self._get_graph(tenant_id)
        
        if not graph.has_node(src):
            self.add_node(tenant_id, src, {"name": src})
        if not graph.has_node(dst):
            self.add_node(tenant_id, dst, {"name": dst})
            
        if graph.has_edge(src, dst):
            existing = graph.edges[src, dst]
            if existing.get('confidence', 0) > metadata.get('confidence', 0):
                logger.warning(f"Conflict detected on edge {src}->{dst}. Keeping existing higher confidence edge.")
                return False
            else:
                logger.info(f"Conflict resolved for {src}->{dst}. Updating with higher confidence data.")
                
        graph.add_edge(src, dst, relationship=relationship_type, **metadata)
        return True
        
    def get_subgraph(self, tenant_id: str, entities: List[str]) -> Dict[str, Any]:
        graph = self._get_graph(tenant_id)
        valid_entities = [e for e in entities if graph.has_node(e)]
        subgraph = graph.subgraph(valid_entities)
        return nx.node_link_data(subgraph)

    def merge_subgraph(self, tenant_id: str, subgraph_data: Dict[str, Any]):
        if not subgraph_data:
            return
        g = nx.node_link_graph(subgraph_data)
        self.graphs[tenant_id] = nx.compose(self._get_graph(tenant_id), g)
        logger.info(f"Merged subgraph into main graph for tenant {tenant_id}.")
