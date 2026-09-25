import networkx as nx
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GraphBuilder:
    """Builds and updates the semantic knowledge graph."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        logger.info("GraphBuilder initialized empty graph.")
        
    def add_node(self, node_id: str, properties: Dict[str, Any]):
        """Add a node representing an entity to the graph."""
        self.graph.add_node(node_id, **properties)
        logger.debug(f"Added node {node_id}")

    def add_edge(self, src: str, dst: str, relationship_type: str, metadata: Dict[str, Any]) -> bool:
        """Add an edge and handle simple conflict detection."""
        if not self.graph.has_node(src):
            self.add_node(src, {"name": src})
        if not self.graph.has_node(dst):
            self.add_node(dst, {"name": dst})
            
        # Conflict detection
        if self.graph.has_edge(src, dst):
            existing = self.graph.edges[src, dst]
            
            # Simple conflict heuristic: if confidence of new is lower, keep old
            if existing.get('confidence', 0) > metadata.get('confidence', 0):
                logger.warning(f"Conflict detected on edge {src}->{dst}. Keeping existing higher confidence edge.")
                return False
            else:
                logger.info(f"Conflict resolved for {src}->{dst}. Updating with higher confidence data.")
                
        self.graph.add_edge(src, dst, relationship=relationship_type, **metadata)
        logger.debug(f"Added edge {src} -> {dst}")
        return True
        
    def get_subgraph(self, entities: List[str]) -> Dict[str, Any]:
        """Extract a subgraph relevant to the provided entities."""
        # Ensure entities exist in the graph
        valid_entities = [e for e in entities if self.graph.has_node(e)]
        subgraph = self.graph.subgraph(valid_entities)
        return nx.node_link_data(subgraph)

    def merge_subgraph(self, subgraph_data: Dict[str, Any]):
        """Merge a cached subgraph back into the main graph."""
        if not subgraph_data:
            return
        g = nx.node_link_graph(subgraph_data)
        self.graph = nx.compose(self.graph, g)
        logger.info(f"Merged subgraph with {len(g.nodes)} nodes into main graph.")
