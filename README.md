# Agent-as-Database: Semantic Knowledge Graph Query Engine

An autonomous research agent that decomposes technical queries into semantic graph operations and fact-finding tasks, maintains knowledge through persistent semantic embeddings with TTL-based caching, detects and resolves conflicting information, and reports query freshness and graph coverage.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [System Components](#system-components)
5. [Usage Examples](#usage-examples)
6. [Caching Strategy](#caching-strategy)
7. [Failure Handling](#failure-handling)
8. [Monitoring & Metrics](#monitoring--metrics)
9. [Data Flow](#data-flow)
10. [Configuration](#configuration)
11. [Development](#development)
12. [Deployment](#deployment)

---

## Overview

### Problem Statement

Traditional agent-based research systems execute queries in isolation:
- Query 1: Research frameworks (3 seconds, 15 API calls)
- Query 2: Research same frameworks (3 seconds, 15 API calls again)
- Query 3: Compare specific subset (3 seconds, 5 new API calls)

**Total**: 9 seconds, 35 API calls, redundant research, no persistent knowledge.

### Our Solution

Agent-as-Database treats agent execution as **graph construction and querying**:
- Query 1: Build knowledge graph (3 seconds, 15 API calls)
- Query 2: Semantic cache hit — reuse 89% of graph (50ms)
- Query 3: Partial cache hit — only research missing edges (1.2s, 5 new API calls)

**Total**: 4.2 seconds, 25 API calls, persistent knowledge, semantic result reuse.

### Key Innovations

1. **Semantic Query Caching** — Cache results by query similarity, not exact string matching
2. **Knowledge Graph Persistence** — Entities and relationships persist across queries
3. **Conflict-Aware Updates** — Detect contradictions and trigger re-verification
4. **Policy-Guided Research** — Learn which tools are most useful for which query types
5. **Observable Traces** — Every decision (cache hit/miss, conflict, resolution) is logged

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                               │
│              "Compare vLLM and Ollama on GPU support"            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │   Query Analyzer (ADK)          │
          │                                 │
          │ - Extract entities             │
          │ - Identify relationships       │
          │ - Generate query embedding     │
          └────────────┬───────────────────┘
                       │
                       ▼
          ┌────────────────────────────────┐
          │  Semantic Cache Lookup         │
          │                                 │
          │ embedding_similarity > 0.75?   │
          │ - Yes: return cached subgraph  │
          │ - No: proceed to planner       │
          └────────────┬───────────────────┘
                       │
              ┌────────┴────────┐
              │ (Cache HIT)     │ (Cache MISS / PARTIAL)
              ▼                 ▼
         [Return]    ┌──────────────────────┐
         [Cached]    │  Query Planner (ADK) │
         [Result]    │                      │
                     │ Generate task DAG:   │
                     │ ├─ Research vLLM GPU │
                     │ ├─ Research Ollama   │
                     │ ├─ Extract features  │
                     │ └─ Compare           │
                     └──────┬───────────────┘
                            │
                            ▼
              ┌─────────────────────────────────┐
              │   Adaptive Tool Selection       │
              │                                  │
              │ Policy Model predicts:          │
              │ P(web_search useful) = 0.92     │
              │ P(github useful) = 0.67         │
              │ P(cache useful) = 0.79          │
              └──────┬──────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │   Task Executor (Workers)     │
         │                               │
         │ Parallel:                     │
         │ ├─ Web Search (timeout: 5s)  │
         │ ├─ GitHub API (timeout: 3s)  │
         │ ├─ Official Docs (retry: 3)  │
         │ └─ Semantic Extract          │
         │                               │
         │ Fault Injection:              │
         │ ├─ Simulate timeout           │
         │ ├─ Malformed response         │
         │ ├─ Empty results              │
         │ └─ API errors                 │
         └───────┬───────────────────────┘
                 │
                 ▼
         ┌─────────────────────────────┐
         │  Evidence Collector         │
         │                             │
         │ Normalize and validate:     │
         │ ├─ Web search results       │
         │ ├─ GitHub metadata          │
         │ ├─ Version information      │
         │ └─ Performance metrics      │
         └───────┬───────────────────┘
                 │
                 ▼
         ┌─────────────────────────────┐
         │  Knowledge Graph Builder    │
         │                             │
         │ Create/Update:              │
         │ ├─ Nodes (concepts)         │
         │ │  └─ {id, name, type,     │
         │ │     metadata, freshness} │
         │ ├─ Edges (relationships)    │
         │ │  └─ {src, dst, type,     │
         │ │     source, confidence}  │
         │ └─ Conflict detection       │
         │    if edge contradiction    │
         └───────┬───────────────────┘
                 │
         ┌───────┴──────────┐
         │                  │
         ▼                  ▼
    [Conflict]         [No Conflict]
    [Detected]         [Continue]
         │                  │
         ▼                  ▼
    ┌──────────┐      ┌──────────────────┐
    │ Verifier │      │ Inference Engine │
    │          │      │                  │
    │Re-search │      │Query graph:      │
    │Resolve   │      │├─ Path finding   │
    └──┬───────┘      │├─ Aggregate      │
       │              │├─ Rank answers   │
       └──────┬───────┤└─ Generate cite  │
              ▼       └──────┬───────────┘
         ┌────────────────────┐
         │ Semantic Cache     │
         │                    │
         │ Store:             │
         │ ├─ Query embedding │
         │ ├─ Result subgraph │
         │ ├─ Freshness date  │
         │ ├─ Hit/miss reason │
         │ └─ TTL (24h)       │
         └────────┬───────────┘
                  │
                  ▼
         ┌─────────────────────┐
         │  Report Generator   │
         │                     │
         │ Output:             │
         │ ├─ Structured JSON  │
         │ ├─ Markdown report  │
         │ ├─ Evidence mapping │
         │ ├─ Freshness score  │
         │ └─ Graph coverage   │
         └────────┬────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │   Trace & Monitoring        │
    │                             │
    │ Record:                     │
    │ ├─ Query → embedding        │
    │ ├─ Cache hit/miss/partial   │
    │ ├─ Tool invocations         │
    │ ├─ Failures & recoveries    │
    │ ├─ Graph operations         │
    │ ├─ Conflicts & resolutions  │
    │ └─ Final metrics            │
    │                             │
    │ Compute:                    │
    │ ├─ Cache hit rate           │
    │ ├─ Tool success rate        │
    │ ├─ Recovery rate            │
    │ ├─ Graph coverage           │
    │ ├─ Answer freshness         │
    │ └─ Conflict resolution %    │
    └─────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip or poetry
- Environment variables: `GOOGLE_API_KEY`, `GITHUB_TOKEN` (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/agent-as-database.git
cd agent-as-database

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Run Your First Query

```bash
# Interactive CLI
python -m src.main cli

# Example prompt:
# > Compare vLLM, Ollama, and llama.cpp for local LLM inference

# Programmatic
python -m src.main query "Compare vLLM and Ollama on GPU support"
```

### View Results

```bash
# Results are stored in outputs/
# - outputs/reports/{query_id}.json (structured)
# - outputs/reports/{query_id}.md (readable)
# - outputs/traces/{query_id}.log (execution trace)
# - outputs/graphs/{query_id}.graphml (knowledge graph)

# View monitoring dashboard
python -m src.dashboard.app
# Open http://localhost:8501
```

---

## System Components

### 1. Query Analyzer (`src/agent/query_analyzer.py`)

**Responsibility**: Parse user input and create semantic representation

**Input**: Natural language query string

**Output**: 
```python
{
  "query_id": "Q-0042",
  "original_text": "Compare vLLM and Ollama on GPU support",
  "entities": [
    {"name": "vLLM", "type": "framework"},
    {"name": "Ollama", "type": "framework"},
    {"name": "GPU support", "type": "capability"}
  ],
  "relationships": [
    {"src": "vLLM", "dst": "GPU support", "type": "has_capability"},
    {"src": "Ollama", "dst": "GPU support", "type": "has_capability"}
  ],
  "embedding": [0.23, 0.45, ..., 0.67],  # 768-dim vector
  "estimated_complexity": "medium",
  "estimated_tool_count": 4
}
```

**Key Methods**:
- `analyze(query: str) -> QueryRepresentation`
- `extract_entities(query: str) -> List[Entity]`
- `extract_relationships(query: str) -> List[Relationship]`
- `embed_query(query: str) -> np.ndarray`

**Tech Stack**: spacy (NLP), sentence-transformers (embeddings)

---

### 2. Semantic Cache (`src/cache/semantic_cache.py`)

**Responsibility**: Store and retrieve cached query results by semantic similarity

**Cache Entry Structure**:
```python
{
  "cache_key": "CACHE-0042",
  "original_query_embedding": [...],
  "query_similarity": 0.89,
  "cached_subgraph": {
    "nodes": [...],
    "edges": [...]
  },
  "cache_hit_type": "full",  # or "partial", "miss"
  "stored_at": "2026-09-24T14:32:00Z",
  "expires_at": "2026-09-25T14:32:00Z",  # TTL: 24h
  "hit_count": 5,
  "last_accessed": "2026-09-24T16:45:00Z"
}
```

**Key Methods**:
- `lookup(query_embedding: np.ndarray, threshold: float = 0.75) -> CacheResult`
- `store(query_embedding, result_subgraph, ttl_hours=24) -> str`
- `invalidate(cache_key: str) -> bool`
- `get_hit_rate() -> float`

**Tech Stack**: Redis (primary), in-memory dict fallback

**TTL Strategy**:
- Framework metadata: 7 days (changes infrequently)
- Performance benchmarks: 3 days (may be updated)
- Community metrics: 1 day (changes frequently)
- Default: 24 hours

---

### 3. Query Planner (`src/agent/query_planner.py`)

**Responsibility**: Decompose query into executable task DAG

**Output Task DAG**:
```python
{
  "plan_id": "PLAN-0042",
  "tasks": [
    {
      "task_id": "T1",
      "description": "Research vLLM GPU support capabilities",
      "tool": "web_search",
      "estimated_time_ms": 2000,
      "priority": 1,
      "dependencies": []
    },
    {
      "task_id": "T2",
      "description": "Fetch Ollama GitHub repository info",
      "tool": "github_api",
      "estimated_time_ms": 1500,
      "priority": 1,
      "dependencies": []
    },
    {
      "task_id": "T3",
      "description": "Extract and compare GPU requirements",
      "tool": "semantic_extract",
      "estimated_time_ms": 500,
      "priority": 2,
      "dependencies": ["T1", "T2"]
    }
  ],
  "total_estimated_time_ms": 4000,
  "parallelizable_tasks": 2,
  "critical_path": ["T1", "T3"]
}
```

**Key Methods**:
- `plan(query_representation: QueryRepresentation) -> TaskDAG`
- `identify_dependencies(tasks: List[Task]) -> Dict[str, List[str]]`
- `estimate_cost(task_dag: TaskDAG) -> Dict[str, float]`

**Tech Stack**: Google ADK (agent definition), networkx (DAG manipulation)

---

### 4. Adaptive Tool Selection (`src/agent/tool_selector.py`)

**Responsibility**: Use learned policy to predict which tools are useful

**Policy Model**:
- Input: Query embedding + historical traces
- Output: P(tool_X useful for this query type)
- Training: Every 50 queries, retrain on recent traces

**Example Predictions**:
```python
{
  "query_type": "framework_comparison",
  "tool_predictions": {
    "web_search": 0.92,      # Official docs found 92% of time
    "github_api": 0.67,       # Repos found 67% of time
    "semantic_cache": 0.79,   # Cache useful 79% of time
    "calculator": 0.15        # Rarely needed
  },
  "recommended_tools": ["web_search", "github_api", "semantic_cache"],
  "skip_tools": ["calculator"],
  "policy_version": "v2.3",
  "policy_updated_at": "2026-09-24T10:00:00Z"
}
```

**Key Methods**:
- `predict_tool_utility(query_embedding: np.ndarray) -> Dict[str, float]`
- `select_tools(predictions: Dict, threshold: float = 0.5) -> List[str]`
- `retrain_policy(traces: List[ExecutionTrace])`

**Tech Stack**: scikit-learn (classifier), joblib (model persistence)

---

### 5. Task Executor (`src/execution/task_executor.py`)

**Responsibility**: Execute tasks with timeout, retry, and fault injection

**Execution Flow**:
```python
for task in task_dag.topological_sort():
    # Check dependencies complete
    if not all(dep_complete for dep in task.dependencies):
        continue
    
    # Set timeout
    with timeout(task.timeout_ms):
        try:
            # Simulate fault (1% chance in production)
            if should_inject_fault():
                raise SimulatedTimeout()
            
            # Execute tool
            result = execute_tool(task.tool, task.inputs)
            
            # Validate output
            if not validate_output(result, task.expected_schema):
                raise MalformedOutputError()
            
            # Store result
            task_results[task.id] = result
            mark_task_complete(task.id)
            
        except TaskTimeout:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                continue  # Retry
            else:
                task_results[task.id] = None
                log_failure(task, "TIMEOUT", retry_count)
                
        except MalformedOutputError:
            if task.fallback_tool:
                task.tool = task.fallback_tool
                continue  # Retry with fallback
            else:
                log_failure(task, "MALFORMED_OUTPUT")
```

**Tool Contracts**:

Each tool must define:
```python
{
  "tool_name": "web_search",
  "timeout_ms": 5000,
  "max_retries": 3,
  "retry_backoff": "exponential",  # base: 1s, multiplier: 2
  "fallback_tool": None,
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "min_length": 1},
      "max_results": {"type": "integer", "minimum": 1, "maximum": 20}
    },
    "required": ["query"]
  },
  "output_schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "snippet": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

**Available Tools**:
1. **web_search** — Google Custom Search API
2. **github_api** — GitHub REST API (repo analysis)
3. **official_docs** — Parse official documentation
4. **semantic_extract** — Extract structured data from text
5. **calculator** — Evaluate mathematical expressions

**Key Methods**:
- `execute_task(task: Task) -> TaskResult`
- `execute_with_timeout(func, timeout_ms)`
- `retry_with_backoff(func, max_retries, backoff_strategy)`
- `validate_output(result, schema) -> bool`

**Tech Stack**: asyncio (concurrent execution), pydantic (validation)

---

### 6. Knowledge Graph Builder (`src/graph/graph_builder.py`)

**Responsibility**: Build and update semantic knowledge graph

**Graph Structure** (NetworkX DiGraph):
```python
# Nodes
graph.add_node(
  node_id="ollama:framework",
  name="Ollama",
  type="framework",
  metadata={
    "official_site": "https://ollama.ai",
    "primary_language": "Go",
    "latest_version": "0.1.48",
    "supported_platforms": ["macOS", "Linux", "Windows"],
    "gpu_support": ["NVIDIA", "AMD", "Metal"],
    "freshness_date": "2026-09-24T00:00:00Z",
    "sources": [
      {
        "url": "https://github.com/ollama/ollama",
        "type": "github",
        "confidence": 0.95
      }
    ]
  }
)

# Edges
graph.add_edge(
  "ollama:framework",
  "nvidia_gpu:hardware",
  relationship_type="supports_gpu",
  metadata={
    "supported_models": ["7B", "13B", "70B"],
    "vram_requirement_gb": 8,
    "source": "https://github.com/ollama/ollama#gpu-acceleration",
    "confidence": 0.88,
    "last_verified": "2026-09-24T10:30:00Z",
    "weight": 0.88
  }
)
```

**Conflict Detection**:
```python
# If adding edge contradicts existing edge:
existing_edge = graph.edges["ollama:framework", "nvidia_gpu:hardware"]
new_edge = ("ollama:framework", "nvidia_gpu:hardware", {"vram_requirement_gb": 4})

if conflict_detected(existing_edge, new_edge):
  conflict_record = {
    "conflict_id": "CONFLICT-0042",
    "entity": "ollama",
    "attribute": "vram_requirement_gb",
    "existing_value": 8,
    "new_value": 4,
    "existing_source": "github.com/ollama/ollama",
    "new_source": "official_blog",
    "status": "unresolved",  # or "resolved_to_new", "resolved_to_existing"
    "resolution_evidence": None
  }
  conflicts.append(conflict_record)
  # Trigger re-verification
```

**Key Methods**:
- `add_node(node_id, properties) -> bool`
- `add_edge(src, dst, relationship_type, metadata) -> bool`
- `detect_conflicts(edge: Edge) -> List[Conflict]`
- `update_node_freshness(node_id, new_freshness_date)`
- `get_subgraph(entities: List[str]) -> DiGraph`
- `query_path(src: str, dst: str) -> List[List[str]]` (find relationships)

**Tech Stack**: NetworkX (graph structure), Python pickle (persistence)

---

### 7. Claim Verifier (`src/verification/verifier.py`)

**Responsibility**: Verify claims against evidence and resolve conflicts

**Verification Workflow**:
```python
for claim in claims_to_verify:
    evidence = find_evidence_for_claim(claim)
    
    if len(evidence) == 0:
        claim.status = "unverified"
        claim.confidence = 0.0
        
    elif len(evidence) == 1:
        claim.status = "verified"
        claim.confidence = evidence[0].confidence
        claim.source = evidence[0].source
        
    else:
        # Multiple sources
        if all_agree(evidence):
            claim.status = "verified"
            claim.confidence = aggregate_confidence(evidence)
        else:
            # Conflict detected
            claim.status = "conflicted"
            claim.conflict_evidence = evidence
            # Trigger re-verification from authoritative source
```

**Key Methods**:
- `verify_claim(claim: str) -> VerificationResult`
- `find_evidence(claim: str, graph: DiGraph) -> List[Evidence]`
- `resolve_conflict(conflicting_evidence: List[Evidence]) -> Evidence`
- `calculate_confidence(evidence_list: List[Evidence]) -> float`

**Tech Stack**: Custom scoring logic, graph traversal

---

### 8. Report Generator (`src/output/report_generator.py`)

**Responsibility**: Generate structured output (JSON + Markdown)

**JSON Report**:
```json
{
  "query_id": "Q-0042",
  "query": "Compare vLLM and Ollama on GPU support",
  "execution_summary": {
    "start_time": "2026-09-24T14:32:00Z",
    "end_time": "2026-09-24T14:32:02.145Z",
    "total_duration_ms": 2145,
    "cache_hit_type": "partial",
    "cache_latency_saved_ms": 1850
  },
  "graph_statistics": {
    "nodes_created": 12,
    "nodes_reused_from_cache": 8,
    "edges_created": 18,
    "edges_reused": 14,
    "graph_coverage": 0.94,
    "total_entities": 20
  },
  "claims": [
    {
      "claim_id": "C001",
      "text": "vLLM supports NVIDIA GPUs",
      "status": "verified",
      "confidence": 0.95,
      "evidence": [
        {
          "type": "official_docs",
          "source": "https://docs.vllm.ai/en/latest/getting_started/installation.html",
          "quote": "vLLM supports NVIDIA GPUs with compute capability 7.0 or higher",
          "freshness": "2026-09-24T00:00:00Z"
        },
        {
          "type": "github",
          "source": "https://github.com/vllm-project/vllm/blob/main/README.md",
          "quote": "NVIDIA GPU (compute capability 7.0+)",
          "freshness": "2026-09-23T15:30:00Z"
        }
      ]
    }
  ],
  "conflicts_detected": 0,
  "conflicts_resolved": 0,
  "tool_invocations": [
    {
      "tool": "web_search",
      "query": "vLLM GPU support NVIDIA",
      "result_count": 5,
      "status": "success",
      "latency_ms": 1200,
      "cache_used": false
    }
  ],
  "recommendations": [
    "Both frameworks support NVIDIA GPUs",
    "Ollama may be easier to set up for beginners",
    "vLLM has better quantization support"
  ],
  "freshness_score": 0.87,
  "answer_quality_estimate": 0.91
}
```

**Markdown Report** (human-readable):
```markdown
# Query Report: Compare vLLM and Ollama on GPU Support

**Query ID**: Q-0042  
**Execution Time**: 2.1 seconds  
**Cache Hit**: Partial (saved 1.8s)

## Answer

### vLLM
- **GPU Support**: ✓ NVIDIA (compute capability 7.0+)
- **Official Docs**: [vllm.ai/getting-started](...)
- **Confidence**: 95%

### Ollama
- **GPU Support**: ✓ NVIDIA, AMD, Metal
- **Official Docs**: [ollama.ai/](...)
- **Confidence**: 92%

## Evidence Map

| Claim | Evidence | Confidence | Freshness |
|-------|----------|------------|-----------|
| vLLM supports NVIDIA | Official docs + GitHub | 95% | Sep 24 |
| Ollama supports NVIDIA | Official docs | 92% | Sep 24 |

## Monitoring

**Cache Performance**: Partial hit (20% from cache, 80% new research)  
**Tool Success Rate**: 100% (4/4 tools succeeded)  
**Recovery Events**: 0  
**Graph Coverage**: 94%

---

*Generated at 2026-09-24 14:32:02 UTC*
```

**Key Methods**:
- `generate_json(execution_trace) -> Dict`
- `generate_markdown(json_report) -> str`
- `generate_graph_visualization(graph) -> str` (Graphviz)

**Tech Stack**: Jinja2 (templates), pydantic (validation)

---

### 9. Trace & Monitoring System (`src/monitoring/tracer.py`)

**Responsibility**: Record every decision and compute metrics

**Trace Entry**:
```python
{
  "trace_id": "TR-0042-001",
  "timestamp": "2026-09-24T14:32:00.123Z",
  "query_id": "Q-0042",
  "event_type": "cache_lookup",
  "details": {
    "query_embedding_shape": [768],
    "cache_candidates": 5,
    "best_match_similarity": 0.89,
    "threshold": 0.75,
    "result": "partial_hit",
    "saved_subgraph_nodes": 8,
    "saved_subgraph_edges": 14,
    "estimated_latency_saved_ms": 1850
  }
}

{
  "trace_id": "TR-0042-002",
  "timestamp": "2026-09-24T14:32:00.234Z",
  "query_id": "Q-0042",
  "event_type": "task_execution",
  "details": {
    "task_id": "T1",
    "tool": "web_search",
    "input": {"query": "vLLM GPU support"},
    "status": "success",
    "latency_ms": 1200,
    "result_count": 5,
    "fault_injected": false
  }
}

{
  "trace_id": "TR-0042-003",
  "timestamp": "2026-09-24T14:32:01.856Z",
  "query_id": "Q-0042",
  "event_type": "graph_operation",
  "details": {
    "operation": "add_edge",
    "src_node": "vllm",
    "dst_node": "nvidia_gpu",
    "relationship": "supports_gpu",
    "conflict_detected": false,
    "edge_confidence": 0.95
  }
}
```

**Computed Metrics**:
```python
{
  "execution_metrics": {
    "total_duration_ms": 2145,
    "planning_time_ms": 234,
    "execution_time_ms": 1856,
    "reporting_time_ms": 55
  },
  "cache_metrics": {
    "cache_hit_rate": 0.33,  # 1/3 queries from cache
    "cache_latency_saved_ms": 1850,
    "cache_cost_reduction": 0.34  # 34% fewer API calls
  },
  "tool_metrics": {
    "total_tool_invocations": 4,
    "successful_invocations": 4,
    "failed_invocations": 0,
    "tool_success_rate": 1.0,
    "average_tool_latency_ms": 950,
    "tool_breakdown": {
      "web_search": {"count": 2, "success_rate": 1.0, "avg_latency_ms": 1100},
      "github_api": {"count": 1, "success_rate": 1.0, "avg_latency_ms": 800},
      "semantic_extract": {"count": 1, "success_rate": 1.0, "avg_latency_ms": 500}
    }
  },
  "fault_recovery_metrics": {
    "faults_injected": 0,
    "faults_detected": 0,
    "recovery_attempts": 0,
    "recovery_success_rate": null,
    "recovery_events": []
  },
  "knowledge_graph_metrics": {
    "nodes_created": 12,
    "nodes_reused": 8,
    "total_nodes_in_graph": 20,
    "edges_created": 18,
    "edges_reused": 14,
    "total_edges_in_graph": 32,
    "graph_coverage_estimate": 0.94,
    "conflicts_detected": 0,
    "conflicts_resolved": 0
  },
  "quality_metrics": {
    "claims_verified": 5,
    "claims_unverified": 0,
    "verification_rate": 1.0,
    "average_claim_confidence": 0.91,
    "freshness_score": 0.87,
    "answer_quality_estimate": 0.91
  }
}
```

**Key Methods**:
- `record_event(event_type: str, details: Dict)`
- `compute_metrics() -> Dict`
- `export_traces(format: str = "json") -> str`
- `analyze_tool_usage() -> Dict`
- `calculate_cache_efficiency() -> float`

**Tech Stack**: JSON lines format, pandas (aggregation)

---

### 10. Monitoring Dashboard (`src/dashboard/app.py`)

**Responsibility**: Visualize metrics and execution traces

**Streamlit Dashboard**:
- Real-time query execution visualization
- Cache hit rate trend chart
- Tool success rate breakdown
- Graph coverage over time
- Conflict resolution success rate
- Query latency distribution
- Recent execution traces (searchable)

---

## Usage Examples

### Example 1: First Query (Cache Miss)

```bash
$ python -m src.main query "Compare Ollama and vLLM for local deployment"

[14:32:00] Starting query analysis...
[14:32:00] Query: "Compare Ollama and vLLM for local deployment"
[14:32:00] Generating query embedding...
[14:32:00] Checking semantic cache...
[14:32:00] Cache: MISS (no similar queries found)
[14:32:00] Generating task plan...

Plan:
  T1: Research Ollama deployment features (web_search)
  T2: Analyze Ollama GitHub repository (github_api)
  T3: Research vLLM deployment features (web_search)
  T4: Analyze vLLM GitHub repository (github_api)
  T5: Compare deployment characteristics (semantic_extract)

[14:32:01] Executing tasks in parallel...
[14:32:01] T1 (web_search: Ollama) → 5 results (1.2s)
[14:32:01] T2 (github_api: Ollama) → metadata retrieved (0.8s)
[14:32:02] T3 (web_search: vLLM) → 5 results (1.1s)
[14:32:02] T4 (github_api: vLLM) → metadata retrieved (0.9s)
[14:32:02] T5 (comparison) → extracted 12 dimensions (0.3s)
[14:32:02] Building knowledge graph...
[14:32:02] Verifying claims...
[14:32:02] Storing in semantic cache...
[14:32:02] Generating report...

✓ Query completed in 2.1 seconds
✓ Graph coverage: 94%
✓ Claims verified: 12/12
✓ Cache entries created: 1

Report saved to: outputs/reports/Q-0042.json
```

### Example 2: Related Query (Partial Cache Hit)

```bash
$ python -m src.main query "What hardware does Ollama support?"

[14:32:05] Starting query analysis...
[14:32:05] Query: "What hardware does Ollama support?"
[14:32:05] Generating query embedding...
[14:32:05] Checking semantic cache...
[14:32:05] Cache: PARTIAL HIT (similarity: 0.89)
[14:32:05] Retrieved 8 nodes and 14 edges from cache

Cached entities reused:
  - Ollama
  - Deployment characteristics
  - Hardware requirements
  - Community metrics

[14:32:05] Identifying missing information...
[14:32:05] Generating targeted task plan...

Plan (focused on gaps):
  T1: Research AMD GPU support (web_search)
  T2: Research Metal GPU support (web_search)
  T3: Verify latest hardware compatibility (official_docs)

[14:32:06] Executing tasks...
[14:32:06] T1 (web_search) → 3 results (1.0s)
[14:32:06] T2 (web_search) → 2 results (0.9s)
[14:32:06] T3 (official_docs) → parsed (0.4s)
[14:32:06] Updating knowledge graph...
[14:32:06] Verifying claims...

✓ Query completed in 1.3 seconds (1.8s saved by cache)
✓ Cache hit type: PARTIAL
✓ New edges added: 6
✓ All claims verified

Report saved to: outputs/reports/Q-0043.json
```

### Example 3: Failure Handling (Simulated)

```bash
$ python -m src.main query "Compare performance benchmarks" --inject-faults

[14:32:10] Starting query analysis...
[14:32:10] Generating task plan...
[14:32:10] Executing tasks with fault injection (1% rate)...

[14:32:11] T2 (web_search) → TIMEOUT after 5000ms
  └─ Retrying with exponential backoff (attempt 1/3)...
  
[14:32:13] T2 (web_search) → SUCCESS (attempt 2)
  └─ Retrieved 4 results after 2.1s retry

[14:32:14] T4 (github_api) → MALFORMED_JSON
  └─ Validating schema... FAILED
  └─ Switching to fallback tool (official_docs)...
  
[14:32:15] T4 (official_docs) → SUCCESS
  └─ Parsed official documentation

[14:32:15] All tasks recovered successfully

✓ Query completed with recovery
✓ Faults injected: 2
✓ Faults recovered: 2
✓ Recovery rate: 100%

Report saved to: outputs/reports/Q-0044.json
```

---

## Caching Strategy

### Semantic Similarity Matching

**Query 1**: "Compare vLLM and Ollama"
→ Embedding: [0.12, 0.45, ..., 0.87]

**Query 2**: "How do vLLM and Ollama differ?"
→ Embedding: [0.14, 0.47, ..., 0.89]

**Cosine Similarity**: 0.89 > threshold (0.75) → **CACHE HIT**

### TTL Strategy

```
Framework metadata:      7 days
Version information:     3 days
Performance benchmarks:  3 days
GPU support info:        3 days
Community metrics:       1 day
API responses:           Default 24h
```

### Cache Invalidation

**Automatic**:
- TTL expiration
- Conflict detected (triggers re-verification)
- Manual invalidation via API

**Monitoring**:
- Cache hit rate trending
- Cache size management
- Stale entry detection

---

## Failure Handling

### Deliberately Induced Failures

**Fault Injection Configuration** (`config/fault_injection.yaml`):
```yaml
fault_injection:
  enabled: true
  injection_rate: 0.01  # 1%
  
  failure_types:
    - type: "timeout"
      probability: 0.4
      affected_tools: ["web_search", "github_api"]
      timeout_ms: 5000
      
    - type: "malformed_response"
      probability: 0.3
      affected_tools: ["github_api", "official_docs"]
      
    - type: "empty_result"
      probability: 0.2
      affected_tools: ["web_search"]
      
    - type: "rate_limit"
      probability: 0.1
      affected_tools: ["web_search", "github_api"]
```

### Recovery Strategies

| Failure Type | Detection | Recovery | Fallback |
|--------------|-----------|----------|----------|
| **Timeout** | latency > timeout_ms | Retry with exponential backoff (3x) | Fallback tool if defined |
| **Malformed JSON** | Schema validation fails | Re-request with error log | Fallback tool |
| **Empty Result** | 0 results returned | Reformulate query | Return "no data" |
| **Rate Limit** | HTTP 429 | Wait + exponential backoff | Fallback tool |
| **Connection Error** | Network unreachable | Retry with exponential backoff | Fallback tool |

### Observable Recovery

Every recovery is traced:
```json
{
  "trace_id": "TR-0042-002",
  "event_type": "fault_injected_and_recovered",
  "details": {
    "task_id": "T1",
    "tool": "web_search",
    "failure_type": "timeout",
    "fault_injected_at": "2026-09-24T14:32:01.100Z",
    "detected_at": "2026-09-24T14:32:06.105Z",
    "recovery_strategy": "retry_with_backoff",
    "retry_attempt": 2,
    "retry_latency_ms": 2150,
    "recovery_success": true,
    "result": "4 search results retrieved"
  }
}
```

---

## Monitoring & Metrics

### Key Performance Indicators (KPIs)

**Tool Metrics**:
- Tool success rate: $$\frac{successful\_calls}{total\_calls}$$
- Tool latency P50/P95/P99: Percentile latency
- Tool retry rate: $$\frac{retried\_calls}{total\_calls}$$

**Cache Metrics**:
- Cache hit rate: $$\frac{cache\_hits}{total\_queries}$$
- Cache latency saved: $$\sum (cached\_latency - retrieval\_latency)$$
- Cache cost reduction: $$\frac{avoided\_api\_calls}{total\_api\_calls}$$

**Recovery Metrics**:
- Recovery rate: $$\frac{successful\_recoveries}{detected\_failures}$$
- Recovery latency overhead: $$\frac{retry\_latency}{original\_latency}$$

**Knowledge Metrics**:
- Graph coverage: $$\frac{retrieved\_entities}{total\_unique\_entities}$$
- Claim verification rate: $$\frac{verified\_claims}{total\_claims}$$
- Conflict resolution success: $$\frac{resolved\_conflicts}{detected\_conflicts}$$

**Answer Quality**:
- Freshness score: Based on entity freshness dates (0-1)
- Citation coverage: $$\frac{cited\_claims}{factual\_claims}$$
- Answer quality estimate: Composite of above metrics (0-1)

### Dashboard (Streamlit)

```
═══════════════════════════════════════════════════════════
               AGENT-AS-DATABASE MONITOR
═══════════════════════════════════════════════════════════

Overall Performance (Last 24h)
├─ Total Queries: 42
├─ Avg Execution Time: 1.8s
├─ Cache Hit Rate: 42.9%
├─ Tool Success Rate: 98.3%
└─ Recovery Rate: 100%

───────────────────────────────────────────────────────────

Tool Performance Breakdown

Web Search          ████████░  (98% success, 1.2s avg)
GitHub API         █████████░  (97% success, 0.9s avg)
Official Docs      ██████████  (100% success, 0.6s avg)
Semantic Extract   █████████░  (99% success, 0.4s avg)
Calculator         ██████████  (100% success, 0.1s avg)

───────────────────────────────────────────────────────────

Cache Statistics

Cache Hits:        18/42 (42.9%)
Partial Hits:      12/42 (28.6%)
Misses:            12/42 (28.6%)
Avg Latency Saved: 1,847 ms/query
Total API Calls Avoided: 156

───────────────────────────────────────────────────────────

Failure & Recovery

Faults Injected:     3
Faults Detected:     3
Successfully Recovered: 3
Recovery Rate:       100%

───────────────────────────────────────────────────────────

Knowledge Graph

Total Nodes:        127
Total Edges:        384
Graph Coverage:     91.2%
Conflicts Detected: 2
Conflicts Resolved: 2

───────────────────────────────────────────────────────────

Recent Queries

Q-0042  "Compare vLLM and Ollama"          ✓ 2.1s   Partial
Q-0043  "Ollama hardware support"          ✓ 1.3s   Partial
Q-0044  "Performance benchmarks"           ✓ 3.2s   Miss
Q-0045  "GPU requirements comparison"      ✓ 0.9s   Full

═══════════════════════════════════════════════════════════
```

---

## Data Flow

### Complete Execution Timeline

```
0ms     ┌─ Query received
        │
        └──→ Query Analyzer (50ms)
             ├─ Extract entities
             ├─ Extract relationships
             └─ Generate embedding
             
50ms    └──→ Semantic Cache (30ms)
             ├─ Lookup similar queries
             └─ RESULT: Partial hit (80% match)
             
80ms    └──→ Query Planner (60ms)
             ├─ Identify missing edges
             ├─ Generate task DAG
             └─ Estimate costs
             
140ms   └──→ Adaptive Tool Selector (20ms)
             └─ Predict tool utility
             
160ms   └──→ Task Executor (parallel: 900ms)
             ├─ T1: web_search (1.2s)
             ├─ T2: github_api (0.8s)
             └─ T3: semantic_extract (0.4s) [depends on T1, T2]
             
1060ms  └──→ Evidence Collector (50ms)
             ├─ Normalize results
             └─ Validate schemas
             
1110ms  └──→ Knowledge Graph Builder (80ms)
             ├─ Add nodes
             ├─ Add edges
             └─ Conflict detection: 0 conflicts
             
1190ms  └──→ Claim Verifier (40ms)
             └─ Verify 12 claims (12/12 verified)
             
1230ms  └──→ Report Generator (60ms)
             ├─ Generate JSON
             └─ Generate Markdown
             
1290ms  └──→ Trace & Monitoring (50ms)
             ├─ Record all events
             └─ Compute metrics
             
1340ms  └─ Response ready
             └─ Total: 1.34s (1.8s saved by cache)
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# APIs
GOOGLE_SEARCH_API_KEY=...
GITHUB_TOKEN=...
OPENAI_API_KEY=...  # For embeddings fallback

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TTL_HOURS=24

# Fault Injection
FAULT_INJECTION_ENABLED=true
FAULT_INJECTION_RATE=0.01

# Monitoring
LOG_LEVEL=INFO
TRACE_EXPORT_FORMAT=json
DASHBOARD_PORT=8501

# Timeouts
TOOL_TIMEOUT_MS=5000
QUERY_TIMEOUT_MS=30000
```

### Configuration File (`config/settings.yaml`)

```yaml
agent:
  max_parallel_tasks: 5
  task_timeout_ms: 5000
  max_retries: 3
  retry_backoff: exponential

cache:
  type: redis
  default_ttl_hours: 24
  ttl_by_entity_type:
    framework_metadata: 7
    version_info: 3
    performance: 3
    community: 1
  semantic_similarity_threshold: 0.75

graph:
  max_nodes: 10000
  max_edges: 50000
  persist_to_disk: true
  disk_path: ./data/graph.pkl

tools:
  web_search:
    timeout_ms: 5000
    max_results: 10
    fallback: null
  github_api:
    timeout_ms: 3000
    max_results: 20
    fallback: official_docs
  official_docs:
    timeout_ms: 4000
    cache_response: true

monitoring:
  enabled: true
  trace_export_format: jsonl
  trace_storage_path: ./outputs/traces/
  metrics_update_interval_ms: 5000
```

---

## Development

### Project Structure

```
agent-as-database/
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── query_analyzer.py   # Parse + embed queries
│   │   ├── query_planner.py    # Generate task DAG
│   │   └── tool_selector.py    # Predict tool utility
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   └── semantic_cache.py   # Query result caching
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── task_executor.py    # Execute tasks with fault handling
│   │   └── tool_implementations.py  # Actual tool code
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   └── graph_builder.py    # Build + maintain knowledge graph
│   │
│   ├── verification/
│   │   ├── __init__.py
│   │   └── verifier.py         # Verify claims + resolve conflicts
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   └── report_generator.py # Generate JSON + Markdown reports
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── tracer.py           # Record execution traces
│   │   └── metrics.py          # Compute KPIs
│   │
│   └── dashboard/
│       ├── __init__.py
│       └── app.py              # Streamlit monitoring dashboard
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_query_analyzer.py
│   │   ├── test_cache.py
│   │   ├── test_graph_builder.py
│   │   └── ...
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_failure_recovery.py
│   └── traces/
│       ├── normal_001.json
│       ├── timeout_001.json
│       ├── malformed_001.json
│       └── ...
│
├── config/
│   ├── settings.yaml           # Main configuration
│   ├── fault_injection.yaml    # Fault scenarios
│   └── tool_contracts.yaml     # Tool schemas
│
├── data/
│   ├── graph.pkl               # Persisted knowledge graph
│   └── cache/                  # Cache backups
│
├── outputs/
│   ├── reports/                # Generated reports (JSON + Markdown)
│   ├── traces/                 # Execution traces
│   └── graphs/                 # Graph exports (GraphML)
│
├── docs/
│   ├── architecture.md         # System design document
│   ├── api.md                  # API reference
│   └── troubleshooting.md      # Common issues
│
├── examples/
│   ├── run_01.md               # Sample execution transcript
│   ├── run_02.md               # With failure recovery
│   └── run_03.md               # Conflict resolution
│
├── .env.example
├── .gitignore
├── requirements.txt
├── setup.py
├── pytest.ini
├── README.md
├── PRD.md                      # Product requirements document
└── CONSTRAINTS.md              # Design constraints
```

### Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=src tests/

# Run specific test
pytest tests/unit/test_cache.py::test_semantic_similarity
```

### Local Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Start Redis (for caching)
docker run -d -p 6379:6379 redis:7

# Run in development mode
python -m src.main query "Your query" --debug

# Start dashboard
python -m src.dashboard.app

# Watch for changes and reload
pytest-watch tests/
```

---

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./outputs:/app/outputs
      - ./data:/app/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  dashboard:
    build: .
    ports:
      - "8501:8501"
    command: streamlit run src/dashboard/app.py
    depends_on:
      - agent
    environment:
      - REDIS_URL=redis://redis:6379/0

volumes:
  redis_data:
```

### Production Deployment

```bash
# Build production image
docker build -t agent-as-database:latest .

# Push to registry
docker push your-registry/agent-as-database:latest

# Deploy to Kubernetes / Cloud Run / etc.
```

---

## Troubleshooting

### Common Issues

**Issue**: Cache not working
```bash
# Check Redis connection
redis-cli PING

# Restart Redis
docker restart redis
```

**Issue**: Tool timeouts
```bash
# Increase timeout in config/settings.yaml
tools:
  web_search:
    timeout_ms: 10000  # increased from 5000
```

**Issue**: Graph too large
```bash
# Prune old cache entries
python -m src.cache.maintenance prune --older-than 30days

# Export graph and start fresh
python -m src.graph.export --format graphml
```

---

## Contributing

This is an internship project. For improvements:

1. Open an issue describing the enhancement
2. Fork the repository
3. Create a feature branch
4. Submit a pull request with test coverage

---

## License

This project is created for educational purposes as part of an internship application.

---

## Contact & Support

For questions about the project architecture, reach out via:
- GitHub Issues
- Project documentation in `/docs/`

**Project Built By**: Ankit (B.Tech AI Student, SRM IST)  
**Last Updated**: September 24, 2026