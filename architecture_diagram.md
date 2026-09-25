# Architecture Diagram: Agent-as-Database

The following diagram illustrates the data flow and core components of the Agent-as-Database system:

```mermaid
graph TD
    User([User Query]) --> Analyzer[Query Analyzer]
    
    Analyzer --> |Extract Entities & Embeddings| Cache[(Semantic Cache)]
    
    Cache -->|Hit > Threshold| CacheHit[Return Cached Subgraph]
    Cache -->|Miss / Partial| Planner[Query Planner]
    
    Planner -->|Generate Task DAG| Selector[Tool Selector]
    
    Selector -->|ML Policy Predictions| Executor[Task Executor]
    
    Executor -->|Tool 1: Web Search| Worker1(Worker)
    Executor -->|Tool 2: GitHub API| Worker2(Worker)
    Executor -->|Tool 3: Extract| Worker3(Worker)
    
    Worker1 --> Builder[Graph Builder]
    Worker2 --> Builder
    Worker3 --> Builder
    
    Builder -->|Insert Nodes/Edges| NetworkX[(Knowledge Graph)]
    
    Builder --> |Detect Conflicts| Verifier[Claim Verifier]
    
    Verifier -->|Resolve & Score| Reporter[Report Generator]
    CacheHit --> Reporter
    
    Reporter -->|Cache Miss/Partial| CacheStore[Store New Subgraph to Cache]
    CacheStore --> Cache
    
    Reporter --> JSON[JSON Report]
    Reporter --> MD[Markdown Report]
    
    Analyzer -.-> |Log Event| Tracer{{Tracer / Telemetry}}
    Cache -.-> |Log Hit/Miss| Tracer
    Planner -.-> |Log DAG| Tracer
    Executor -.-> |Log Failures/Retries| Tracer
    Builder -.-> |Log Conflicts| Tracer
```

### Component Details
- **Query Analyzer**: Uses SpaCy for NLP extraction and sentence-transformers for vector embeddings.
- **Semantic Cache**: Redis-backed cache that matches identical semantic intents using cosine similarity (e.g. `Similarity > 0.75`).
- **Query Planner**: Decomposes intents into an acyclic graph of actionable tool requests.
- **Task Executor**: A robust tool runner that implements exponential backoff, fault-injection, and fallback strategies.
- **Knowledge Graph**: A `NetworkX` directed graph that tracks entity relationships and monitors edge-level contradictions.
- **Tracer**: Observability module logging structured telemetry for cache hit rates and system performance monitoring.
