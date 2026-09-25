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
        """
        Extract named entities and domain-specific keywords.
        Uses SpaCy NER first, then noun-chunk fallback to ensure
        non-empty entity lists for any well-formed query.
        """
        entities = []
        seen = set()
        hardware_kw = {"gpu", "nvidia", "amd", "metal", "cuda", "tpu", "cpu"}

        if self.nlp:
            doc = self.nlp(query)

            # 1. Named Entity Recognition
            for ent in doc.ents:
                key = ent.text.lower()
                if key not in seen:
                    seen.add(key)
                    entities.append(Entity(name=ent.text, type=ent.label_.lower()))

            # 2. Token-level tech keyword scan
            for token in doc:
                key = token.text.lower()
                if key not in seen:
                    if key in hardware_kw:
                        seen.add(key)
                        entities.append(Entity(name=token.text, type="hardware"))

            # 3. Noun-chunk fallback — catches "Redis", "Memcached", "vLLM" etc.
            #    Only activates when NER found nothing useful.
            if not entities:
                stop_words = {"what", "how", "does", "is", "are", "the", "a", "an",
                              "and", "or", "for", "to", "of", "in", "on", "at",
                              "compare", "difference", "between", "vs", "versus",
                              "tell", "me", "about", "explain", "use", "used",
                              "with", "from", "than", "that", "this"}
                for chunk in doc.noun_chunks:
                    key = chunk.root.text.lower()
                    if key not in stop_words and key not in seen and len(key) > 2:
                        seen.add(key)
                        entities.append(Entity(name=chunk.root.text, type="concept"))
        else:
            # No SpaCy — basic whitespace tokeniser
            for w in query.split():
                clean = w.strip(",.?!").lower()
                if len(clean) > 3 and clean not in seen:
                    seen.add(clean)
                    entities.append(Entity(name=w.strip(",.?!"), type="concept"))

        logger.debug(f"Extracted {len(entities)} entities: {[e.name for e in entities]}")
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
