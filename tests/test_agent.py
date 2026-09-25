import pytest
from src.agent.types import QueryRepresentation, Entity
from src.agent.query_planner import QueryPlanner
from src.cache.semantic_cache import SemanticCache

def test_query_planner_multiple_entities():
    planner = QueryPlanner()
    query = QueryRepresentation(
        query_id="Q-TEST",
        original_text="Compare vLLM and Ollama",
        entities=[
            Entity(name="vLLM", type="framework"),
            Entity(name="Ollama", type="framework")
        ]
    )
    plan = planner.plan(query)
    
    # 2 entity research tasks + 1 semantic extraction task
    assert len(plan.tasks) == 3
    assert plan.tasks[-1].tool == "semantic_extract"
    assert len(plan.tasks[-1].dependencies) == 2

def test_query_planner_single_entity():
    planner = QueryPlanner()
    query = QueryRepresentation(
        query_id="Q-TEST2",
        original_text="What is vLLM?",
        entities=[
            Entity(name="vLLM", type="framework")
        ]
    )
    plan = planner.plan(query)
    
    # Only 1 research task
    assert len(plan.tasks) == 1
    assert plan.tasks[0].tool == "web_search"
    assert len(plan.tasks[0].dependencies) == 0

def test_semantic_cache_miss():
    # Cache initialized with no Redis available will fall back to in-memory
    cache = SemanticCache(similarity_threshold=0.75)
    
    dummy_embedding = [0.1] * 768
    result = cache.lookup(dummy_embedding)
    
    assert result is None
