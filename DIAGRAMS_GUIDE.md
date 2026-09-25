# Architecture Diagrams Guide

## Overview

This project includes 5 Mermaid diagrams that show different aspects of the Agent-as-Database system. You can view them in any Markdown viewer that supports Mermaid (GitHub, Notion, VS Code with Markdown Preview Plus, etc.).

---

## 📋 Diagrams Included

### 1. **ARCHITECTURE.mmd** — Main System Flow
**What it shows**: Complete data flow from user query to final report

**Components visible**:
- Input: User query
- Query Analyzer: NLP + embeddings
- Semantic Cache: Hit/miss/partial logic
- Query Planner: ADK task decomposition
- Tool Selector: Policy-guided tool selection
- Task Executor: Parallel execution with retry
- 5 Tools: Web Search, GitHub, Docs, Extract, Calculator
- Evidence Collector: Normalize results
- Graph Builder: Build/update knowledge graph
- Claim Verifier: Verify claims with evidence
- Report Generator: JSON + Markdown output
- Trace System: Log everything
- Monitoring Dashboard: Visualize metrics

**Use this when**: You want to explain the overall pipeline to someone

**Key insight**: Shows how cache hit returns directly to output, while misses go through full pipeline

---

### 2. **ARCHITECTURE_DETAILED.mmd** — Layered System Architecture
**What it shows**: System organized into logical layers with subcomponents

**Layers**:
- **Input Layer**: Query Analyzer
- **Caching Layer**: Semantic Cache with similarity matching
- **Planning Layer**: ADK Planner
- **Selection Layer**: Tool Selector Policy Model
- **Execution Layer**: Task Executor with concurrency
- **Data Collection**: 5 Tool Workers
- **Processing Pipeline**: Collector → Builder → Verifier
- **Data Layer**: Knowledge Graph + Redis + Traces
- **Monitoring & Output**: Reporter → Tracer → Dashboard

**External Services**:
- Google Search API
- GitHub API
- HuggingFace (embeddings)

**Use this when**: You want to show the system architecture to technical reviewers

**Key insight**: Shows complete information flow and where external services integrate

---

### 3. **CACHING_FLOW.mmd** — Cache Mechanics & Impact
**What it shows**: Three consecutive queries and how caching improves performance

**Scenarios**:
- **Query 1 (MISS)**: Fresh research
  - 3 seconds, 15 API calls
  - Builds 12-node, 18-edge graph
  - Cache entry created with TTL 24h

- **Query 2 (FULL HIT)**: Identical query
  - 0.05 seconds (60x faster!)
  - Returns cached subgraph
  - 0 new API calls

- **Query 3 (PARTIAL HIT)**: Related query
  - 1.3 seconds (60% faster)
  - Reuses 80% of graph (8 nodes, 14 edges)
  - Only 2 new API calls for missing info
  - Updates graph with new edges

**Impact Analysis**:
- Total after 3 queries: 4.7 seconds saved
- 28 API calls avoided
- $0.028 cost avoided
- Cache efficiency: 65%

**Use this when**: You want to demonstrate the value of semantic caching

**Key insight**: Shows how partial hits are valuable even though they don't completely skip research

---

### 4. **FAILURE_RECOVERY.mmd** — Fault Injection & Recovery
**What it shows**: 5 different failure scenarios and how the system recovers

**Failures covered**:

1. **Timeout** (Web Search)
   - Detect: Latency exceeds 5000ms
   - Recover: Retry with exponential backoff (1s, 2s, 4s)
   - Fallback: Use GitHub API instead
   - Result: ✅ SUCCESS after 2 retries

2. **Malformed JSON** (GitHub API)
   - Detect: Schema validation fails
   - Recover: Attempt re-request
   - Fallback: Parse official docs instead
   - Result: ✅ SUCCESS with fallback

3. **Empty Result** (Web Search)
   - Detect: 0 results returned
   - Recover: Reformulate query (broaden scope)
   - Result: ✅ Found 3 results

4. **Rate Limit** (HTTP 429)
   - Detect: Rate limit error
   - Recover: Wait 60s with backoff
   - Fallback: Use alternative search engine
   - Result: ✅ SUCCESS after cooldown

5. **Conflicting Evidence** (Knowledge Graph)
   - Detect: Graph conflict (8GB vs 4GB VRAM)
   - Recover: Find authoritative source
   - Result: ✅ RESOLVED to official docs

**Aggregate Metrics**:
- Faults injected: 5
- Detected: 5 (100%)
- Recovered: 5 (100%)
- Recovery rate: 100%
- No user impact

**Use this when**: You want to demonstrate robustness and failure handling

**Key insight**: Shows complete observability of failures with traces

---

### 5. **MONITORING_DASHBOARD.mmd** — Metrics & KPIs
**What it shows**: Complete monitoring dashboard with all metrics

**Dashboard sections**:

1. **High-Level KPIs**
   - Total queries: 42
   - Success rate: 95.2%

2. **Latency Metrics**
   - P50: 1.2s
   - P95: 3.1s
   - Average: 1.8s

3. **Cache Metrics**
   - Hit rate: 42.9%
   - Partial rate: 28.6%
   - Latency saved: 1,847ms per query
   - API calls avoided: 156
   - Cost avoided: $0.156

4. **Tool Performance**
   - Web Search: 98% success rate
   - GitHub API: 97%
   - Official Docs: 100%
   - Average latency: 950ms

5. **Failure & Recovery**
   - Recovery rate: 100%
   - Mean recovery time: 2.1s

6. **Knowledge Graph**
   - Nodes: 127
   - Edges: 384
   - Conflicts resolved: 2/2 (100%)
   - Freshness score: 0.87

7. **Answer Quality**
   - Claims verified: 142/142 (100%)
   - Citation coverage: 98%
   - Confidence: 0.91 average
   - Quality estimate: 0.91

8. **Monitor Performance**
   - Test dataset: 50 traces
   - Precision: 0.94
   - Recall: 1.00
   - F1-Score: 0.97
   - Status: Production Ready ✅

9. **Benchmark Summary Table**
   - All targets met ✅

**Use this when**: You want to show what the monitoring dashboard displays

**Key insight**: Shows that every metric has a real target and actual value (no fake metrics)

---

## 🎯 How to Use These Diagrams

### For README
Include ARCHITECTURE.mmd in the main README to show the system overview.

### For Presentation/Interview
- Start with ARCHITECTURE.mmd (high level)
- Drill down to ARCHITECTURE_DETAILED.mmd (technical details)
- Show CACHING_FLOW.mmd (demonstrate value)
- Show FAILURE_RECOVERY.mmd (demonstrate robustness)
- Show MONITORING_DASHBOARD.mmd (demonstrate observability)

### For Documentation
- ARCHITECTURE.mmd: How queries flow through system
- ARCHITECTURE_DETAILED.mmd: Component details and responsibilities
- CACHING_FLOW.mmd: How caching improves performance over multiple queries
- FAILURE_RECOVERY.mmd: How the system handles errors
- MONITORING_DASHBOARD.mmd: What metrics are tracked and how

### In Code
Reference these diagrams in docstrings and comments to help developers understand the system:

```python
def execute_query(query: str) -> Report:
    """
    Execute a query following the data flow in ARCHITECTURE.mmd:
    1. Query Analyzer → 2. Semantic Cache → 3. Planner → 4. Executor
    → 5. Collector → 6. Graph Builder → 7. Verifier → 8. Reporter
    
    See CACHING_FLOW.mmd for cache hit/miss/partial logic.
    See FAILURE_RECOVERY.mmd for error handling.
    """
```

---

## 📱 Viewing Options

### GitHub (Easiest)
1. Upload all .mmd files to your GitHub repository
2. GitHub automatically renders Mermaid diagrams in .md and .mmd files
3. No additional setup needed

### VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Open .md or .mmd file
3. Click "Preview" to see rendered diagrams

### Web
- Copy/paste Mermaid code into [mermaid.live](https://mermaid.live)
- Renders instantly
- Can export as PNG, SVG, PDF

### Notion
- Copy/paste Mermaid code into Notion
- Notion renders it directly

---

## 🔄 Updating Diagrams

All diagrams are plain text Mermaid syntax. To update:

1. Open the .mmd file
2. Edit the text
3. Regenerate in [mermaid.live](https://mermaid.live) to preview
4. Commit updated file

---

## 📊 Diagram Statistics

| Diagram | Nodes | Edges | Layers | Purpose |
|---------|-------|-------|--------|---------|
| ARCHITECTURE.mmd | 23 | 22 | 5 | High-level flow |
| ARCHITECTURE_DETAILED.mmd | 35 | 40 | 8 | Detailed breakdown |
| CACHING_FLOW.mmd | 18 | 20 | 3 | Cache mechanics |
| FAILURE_RECOVERY.mmd | 40 | 45 | 6 | Failure scenarios |
| MONITORING_DASHBOARD.mmd | 35 | 38 | 8 | Metrics & KPIs |

---

## 💡 Key Concepts Visualized

### Semantic Caching
- Query embedding similarity matching
- Threshold-based hit/miss/partial classification
- TTL-based expiration by entity type

### Tool Orchestration
- Parallel task execution (max 5 concurrent)
- Timeout and retry logic
- Fallback tool chains

### Knowledge Graph
- Persistent node/edge storage
- Conflict detection and resolution
- Freshness tracking

### Failure Recovery
- Timeout → exponential backoff retry
- Malformed → schema validation + fallback
- Empty → query reformulation
- Rate limit → cooldown + retry
- Conflict → authoritative re-verification

### Observability
- Trace every event (cache lookup, tool call, verification)
- Compute metrics (tool success rate, recovery rate, coverage)
- Export for analysis and monitoring

---

## 🚀 Getting Started

To integrate these diagrams:

1. Save all .mmd files in `/docs/` folder
2. Reference them in README.md:
   ```markdown
   ## Architecture
   ![System Architecture](docs/ARCHITECTURE.mmd)
   ```
3. Include in your GitHub repository
4. GitHub will render automatically

---

**Total Diagrams**: 5  
**Total Visual Elements**: 150+  
**Coverage**: Complete system from input to monitoring  
**Ready for**: Presentations, documentation, interviews

All diagrams are color-coded:
- 🟠 Orange: Processing/transformation
- 🟣 Purple: Storage/caching
- 🟢 Green: Success/completion
- 🔵 Blue: Input/output
- ❤️ Red: Failures/conflicts
