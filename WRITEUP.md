# Design Write-up: Agent-as-Database

## Domain and Goal

The agent targets **competitive framework research** — given a natural language query like
"Compare vLLM and Ollama on GPU support", it autonomously decomposes the goal, retrieves
live data from public sources, constructs a knowledge graph of entities and relationships,
verifies claims for contradictions, and produces a structured JSON and Markdown report.

---

## Key Design Decisions

**1. DAG-Based Task Planning**
Instead of a flat sequential pipeline, the QueryPlanner emits a directed acyclic graph (DAG)
of tasks. This makes dependency relationships explicit and enables future parallelism. Each
node in the DAG has a declared tool, inputs, and a retry budget. The planner logs its full
structure before execution begins, satisfying the requirement for a visible planning trace.

**2. Semantic Cache as the Primary Optimization**
The most expensive operation in any research agent is redundant tool invocation. A
sentence-transformers embedding (all-MiniLM-L6-v2, 384-dim) is computed for every query.
Subsequent queries with cosine similarity >= 0.75 retrieve a cached subgraph instead of
re-executing the DAG. Full hits (>= 0.95 similarity) are served in under 30ms. The cache is
partitioned by tenant_id to enforce isolation in multi-user deployments.

**3. Knowledge Graph Persistence (NetworkX)**
Execution results are not discarded. Verified claims are materialized as nodes and typed
edges in a NetworkX DiGraph, keyed per tenant. On edge insertion, the builder checks for
conflicting claims (same source/target, different relationship). Higher-confidence edges win.
This graph accumulates value across queries rather than treating each run as stateless.

**4. Modular Tool Registry**
Tools are registered by name into a dictionary rather than hardcoded into the executor.
This means new tools (including MCP-compliant external servers) can be injected at runtime
without modifying the orchestrator. The web_search tool currently calls the Wikipedia API
with proper URL encoding and a User-Agent header. github_api and semantic_extract use
deterministic mock responses with injected latency to simulate real network behaviour for
testing purposes.

**5. FastAPI Production Layer**
The agent is exposed via a FastAPI server with Bearer token authentication. Each token maps
to a tenant_id, scoping both the semantic cache and the knowledge graph. This satisfies the
Phase 2 production requirement and allows the Streamlit ops console to communicate with the
agent over HTTP rather than importing it directly.

---

## Limitations

- **Mock tool data**: github_api and semantic_extract return deterministic mock responses.
  Real implementations would require authenticated API keys and rate-limit handling.
- **LLM verification is simulated**: The ClaimVerifier's Chain-of-Thought reasoning is
  currently a stub. A real implementation would call an LLM (e.g., Claude or GPT-4) with
  a structured prompt to evaluate claim consistency against retrieved evidence.
- **In-memory cache resets on restart**: Without a running Redis instance, the semantic
  cache uses a Python dict. All cache entries are lost on server restart.
- **Single-node graph**: NetworkX holds the entire graph in memory. For large corpora this
  would need to be replaced with a graph database (e.g., Neo4j).

---

## What I Would Do Differently With More Time

1. Wire the ClaimVerifier to a real LLM API for genuine contradiction detection.
2. Replace mock tool responses with authenticated calls to GitHub API and a search engine.
3. Persist the knowledge graph to disk (GraphML or Neo4j) so state survives restarts.
4. Add a proper evaluation harness: given a known-answer query set, measure precision and
   recall of the verified claims against ground truth.
5. Implement the multi-agent debate mechanism for Phase 3 conflict resolution.
