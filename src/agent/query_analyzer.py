import uuid
import logging
from typing import List
from .types import QueryRepresentation, Entity, Relationship

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    """Parses natural language queries and creates semantic representations."""
    
    def __init__(self):
        try:
            import spacy
            from sentence_transformers import SentenceTransformer
            # Note: requires running `python -m spacy download en_core_web_sm`
            self.nlp = spacy.load("en_core_web_sm")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("QueryAnalyzer initialized with spaCy and sentence-transformers.")
        except ImportError:
            logger.warning("spacy or sentence-transformers not installed. Using fallback logic.")
            self.nlp = None
            self.embedder = None
        except OSError:
            logger.warning("spaCy en_core_web_sm model not found. Using fallback logic.")
            self.nlp = None
            self.embedder = None # Assuming if spacy is missing, we might want to fallback entirely or handle carefully.
            
    def analyze(self, query: str) -> QueryRepresentation:
        """Process natural language query and return typed semantic representation."""
        query_id = f"Q-{uuid.uuid4().hex[:4].upper()}"
        
        logger.debug(f"Analyzing query: {query}")
        entities = self.extract_entities(query)
        relationships = self.extract_relationships(query)
        embedding = self.embed_query(query)
        
        return QueryRepresentation(
            query_id=query_id,
            original_text=query,
            entities=entities,
            relationships=relationships,
            embedding=embedding,
            estimated_complexity="high" if len(entities) > 2 else "medium",
            estimated_tool_count=len(entities) + 1
        )

    def extract_entities(self, query: str) -> List[Entity]:
        """Extract named entities and domain-specific keywords."""
        entities = []
        tech_keywords = ["vllm", "ollama", "llama.cpp", "gpu", "nvidia", "amd", "metal", "cuda"]
        
        if self.nlp:
            doc = self.nlp(query)
            for ent in doc.ents:
                entities.append(Entity(name=ent.text, type=ent.label_.lower()))
                
            # Domain specific extraction fallback
            for token in doc:
                text_lower = token.text.lower()
                if text_lower in tech_keywords and not any(e.name.lower() == text_lower for e in entities):
                    ent_type = "hardware" if text_lower in ["gpu", "nvidia", "amd", "metal", "cuda"] else "framework"
                    entities.append(Entity(name=token.text, type=ent_type))
        else:
            # Simple fallback
            words = query.split()
            for w in words:
                clean_w = w.strip(",.?!").lower()
                if clean_w in tech_keywords:
                    ent_type = "hardware" if clean_w in ["gpu", "nvidia", "amd", "metal", "cuda"] else "framework"
                    entities.append(Entity(name=w, type=ent_type))
                    
        return entities

    def extract_relationships(self, query: str) -> List[Relationship]:
        """Identify semantic relationships between extracted entities."""
        # Stub for relationship extraction (would use dependency parsing)
        return []

    def embed_query(self, query: str):
        """Generate dense vector embedding for semantic matching."""
        if self.embedder:
            return self.embedder.encode(query).tolist()
        return [0.0] * 768  # Mock 768-dimensional embedding
