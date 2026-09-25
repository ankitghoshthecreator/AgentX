# Design Constraints & Engineering Discipline

**Document Purpose**: Define what "senior-level engineering" means for this project.  
**Audience**: Code reviewers, collaborators, future maintainers  
**Status**: Binding for all code changes

---

## Philosophy

This project should feel **deliberately engineered**, not **hastily assembled**.

Code speaks louder than marketing. A clean, modular system with thoughtful error handling and comprehensive documentation shows engineering maturity far better than buzzwords, gradients, or fake testimonials ever could.

---

## SECTION 1: DOS (Engineering Excellence)

### DO: Write Production-Grade Code

#### DO: Modular Architecture
- **Principle**: Each component has a single, clear responsibility
- **Implementation**:
  - Query analyzer handles NLP only
  - Cache handles caching only
  - Executor handles execution only
  - No component should know the implementation details of another
- **Guideline**: If a file > 500 lines or a function > 50 lines, refactor it
- **Check**: `grep -r "import src\." src/ | head -20` should show clean separation

#### DO: Type Hints on Everything
```python
# BAD
def process_query(q):
    return results

# GOOD
def process_query(q: str) -> List[QueryResult]:
    """Process natural language query and return typed results."""
    return results
```
- Every function parameter and return type must be annotated
- Use `from typing import *` for complex types
- Run mypy regularly: `mypy src/ --ignore-missing-imports`

#### DO: Comprehensive Error Handling
```python
# BAD
try:
    result = web_search(query)
except Exception:
    pass  # Silently fail

# GOOD
try:
    result = web_search(query)
except requests.Timeout as e:
    logger.warning(f"Web search timeout for '{query}': {e}")
    self.trace.record_event("web_search_timeout", {"query": query})
    return self._fallback_tool(query)
except requests.HTTPError as e:
    if e.response.status_code == 429:
        logger.warning("GitHub rate limit hit, waiting...")
        time.sleep(60)
        return self._retry_with_backoff(web_search, query)
    else:
        raise
except Exception as e:
    logger.error(f"Unexpected error in web_search: {e}", exc_info=True)
    raise
```
- Every exception must be caught and handled explicitly
- Use specific exception types, never bare `except Exception`
- Always log failures with context
- Record failures in trace system

#### DO: Testable Code
- Every component must be testable in isolation
- Use dependency injection (pass dependencies as arguments)
- Mock external services (APIs, Redis, etc.)
- Aim for > 80% test coverage

```python
# BAD (hard to test)
class QueryAnalyzer:
    def __init__(self):
        self.model = load_model()  # Direct dependency
        
    def analyze(self, query):
        return self.model.process(query)

# GOOD (testable)
class QueryAnalyzer:
    def __init__(self, embedding_model: EmbeddingModel):
        self.model = embedding_model  # Injected dependency
        
    def analyze(self, query: str) -> QueryRepresentation:
        return self.model.process(query)

# In tests:
mock_model = Mock(spec=EmbeddingModel)
analyzer = QueryAnalyzer(embedding_model=mock_model)
result = analyzer.analyze("test query")
mock_model.process.assert_called_once_with("test query")
```

#### DO: Meaningful Variable Names
```python
# BAD
def f(x, y):
    return x + y

q = "compare frameworks"
r = analyze(q)

# GOOD
def calculate_total_cost(base_cost: float, tax_rate: float) -> float:
    return base_cost + (base_cost * tax_rate)

user_query = "compare frameworks"
query_analysis_result = analyze(user_query)
```
- Variable names should describe their content, not their type
- Avoid single-letter names except in mathematical contexts
- Use full words, not abbreviations (except common ones: db, api, url)

#### DO: Docstrings on All Public Functions
```python
def verify_claim(claim: str, graph: nx.DiGraph) -> VerificationResult:
    """
    Verify a factual claim against evidence in the knowledge graph.
    
    Args:
        claim: The factual statement to verify (e.g., "vLLM supports NVIDIA GPUs")
        graph: The knowledge graph containing entities and relationships
        
    Returns:
        VerificationResult containing:
        - status: "verified", "unverified", or "conflicted"
        - confidence: Float from 0.0 (no evidence) to 1.0 (certain)
        - evidence: List of supporting sources
        - conflicting_evidence: If status=="conflicted", list of contradictory sources
        
    Raises:
        ValueError: If claim is empty or graph is None
        
    Example:
        >>> result = verify_claim("Ollama supports GPU", my_graph)
        >>> print(result.status)
        'verified'
    """
    if not claim or graph is None:
        raise ValueError("claim and graph cannot be None")
    # ... implementation
```

#### DO: Structured Logging
```python
# BAD
print("Query processed")
logger.info("Query: " + query + " took " + str(time) + "ms")

# GOOD
import structlog

logger = structlog.get_logger()
logger.info(
    "query_processed",
    query=query,
    duration_ms=elapsed_time,
    result_count=len(results),
    cache_hit=was_cache_hit
)
```
- Use structured logging (JSON lines format)
- Every log entry should be machine-parseable
- Include relevant context (IDs, counts, metrics)
- Use appropriate log levels: DEBUG < INFO < WARNING < ERROR < CRITICAL

#### DO: Configuration Management
```python
# BAD - Hardcoded values
TIMEOUT_MS = 5000
RETRY_COUNT = 3

# GOOD - Configuration from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    tool_timeout_ms: int = 5000  # Default, override via env
    max_retries: int = 3
    redis_url: str = "redis://localhost:6379/0"
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"
        
settings = Settings()
```
- All configurable values go in config files or environment variables
- Never hardcode API keys, timeouts, or feature flags
- Support environment-specific configs (dev, test, prod)

#### DO: Comprehensive Documentation
- README: How to install, run, use the system
- Architecture: High-level component diagram + data flow
- API docs: Function signatures, parameters, return types
- Design decisions: Why this approach, what alternatives were considered
- Troubleshooting: Common errors and how to fix them

---

### DO: Demonstrate Engineering Practices

#### DO: Version Control Discipline
```bash
# Good commit messages
git commit -m "Implement semantic cache lookup with cosine similarity"
git commit -m "Add exponential backoff retry logic to task executor"
git commit -m "Fix: handle malformed JSON responses in GitHub API tool"

# BAD commit messages
git commit -m "fixes"
git commit -m "working version"
git commit -m "WIP"
```

#### DO: Testing Strategy
```python
# tests/unit/test_cache.py
def test_semantic_cache_full_hit():
    """Test that similar queries hit cache with similarity > threshold."""
    cache = SemanticCache(similarity_threshold=0.75)
    
    # Store first query
    embedding_1 = np.array([0.1, 0.2, ..., 0.9])
    result_1 = {"answer": "vLLM supports GPU", "confidence": 0.95}
    cache.store(embedding_1, result_1)
    
    # Similar query (cosine sim: 0.89)
    embedding_2 = np.array([0.11, 0.21, ..., 0.91])
    
    # Lookup should hit
    hit = cache.lookup(embedding_2)
    assert hit is not None
    assert hit.query_similarity >= 0.75
    assert hit.result == result_1

def test_semantic_cache_miss():
    """Test that dissimilar queries miss cache."""
    cache = SemanticCache(similarity_threshold=0.75)
    
    embedding_1 = np.array([0.1, 0.2, ..., 0.9])
    cache.store(embedding_1, {"answer": "A"})
    
    embedding_2 = np.array([0.9, 0.8, ..., 0.1])  # Opposite embedding
    
    hit = cache.lookup(embedding_2)
    assert hit is None

# tests/integration/test_end_to_end.py
def test_full_query_execution():
    """Integration test: query → plan → execute → report."""
    agent = Agent(config=test_config)
    
    result = agent.execute_query("Compare vLLM and Ollama")
    
    assert result.status == "success"
    assert result.execution_time_ms < 5000
    assert len(result.claims) > 0
    assert all(claim.confidence > 0 for claim in result.claims)
```

#### DO: Monitor and Measure
- Track metrics continuously (cache hit rate, latency, success rate)
- Compare against targets
- Use measurements to drive improvements
- Export metrics for analysis

#### DO: Graceful Degradation
```python
# If cache unavailable, continue with fresh research
try:
    cached_result = cache.lookup(query_embedding)
    return cached_result
except redis.ConnectionError:
    logger.warning("Cache unavailable, proceeding with full research")
    return full_research(query)

# If GitHub API fails, use web search instead
try:
    result = github_tool(url)
except GitHubApiError:
    logger.info("GitHub API unavailable, using fallback web search")
    return web_search(f"{repo_name} github")
```

---

### DO: Build for Observability

#### DO: Comprehensive Tracing
Every decision should be logged:
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
    "result": "partial_hit"
  }
}
```

#### DO: Metrics Export
- Export metrics in standard formats (Prometheus, JSON)
- Make metrics queryable and visualizable
- Track trends over time
- Alert on anomalies

---

### DO: Respect User Time

#### DO: Fast Execution
- Optimize critical paths
- Measure and report latency
- Cache aggressively
- Run tasks in parallel when possible

#### DO: Clear Feedback
- Show progress (execution trace)
- Explain decisions (why was this tool chosen)
- Report results clearly (evidence mapping)
- Provide next steps

---

## SECTION 2: DONTS (Anti-Patterns)

### DON'T: Prioritize Aesthetics Over Substance

#### ❌ DON'T: Use Purple Gradients
```css
/* FORBIDDEN */
background: linear-gradient(135deg, #9c27b0, #673ab7);
background: linear-gradient(to right, #e91e63, #9c27b0);
```
**Reason**: Gradients are visual noise. They don't convey information.  
**Use Instead**: Solid, accessible colors (white background, dark text). Let functionality speak.

#### ❌ DON'T: Vague Hero Text
```
FORBIDDEN:
"Intelligent agents that think"
"AI that understands you"
"Next-generation autonomous systems"

USE INSTEAD:
"Semantic knowledge graph query engine with cache and failure recovery"
"Research agent that learns from prior queries and handles timeouts"
```
**Reason**: Vague claims erode trust. Specific descriptions demonstrate understanding.

#### ❌ DON'T: Fake Customer Testimonials
```
FORBIDDEN:
"★★★★★ 'This changed everything!' - Sarah, CEO"
"★★★★★ 'Amazing results!' - John, from startup"
(With no link, no verification, no date)
```
**Reason**: Fake testimonials are dishonest. Real metrics are more credible.

#### ❌ DON'T: X-Rake Reviews
```
FORBIDDEN (too many stars, fake data):
"★★★★★ Helped me save 10,000 hours!"
"★★★★★ Increased revenue by 500%"
"★★★★★ Changed my life"
```
**Reason**: Unsubstantiated claims damage credibility.  
**Use Instead**: Specific, measurable results:
- "Cache hit rate: 42.9% after 50 queries"
- "Tool success rate: 98.3%"
- "Average latency: 1.3 seconds (partial cache hit)"

#### ❌ DON'T: Too Much Scroll Animation
```javascript
// FORBIDDEN
window.addEventListener('scroll', () => {
  element.style.transform = `rotate(${window.scrollY * 2}deg)`;
  element.style.opacity = Math.sin(window.scrollY / 100);
  element.style.scale = 1 + (window.scrollY / 500);
});
```
**Reason**: Animations distract from content. They make the page slow.  
**Use Instead**: Static layout, fast load time. Let the data speak.

#### ❌ DON'T: Pill-Shaped Buttons
```css
/* FORBIDDEN */
button {
  border-radius: 50px;  /* Full pill shape */
  background: linear-gradient(135deg, #ff6b6b, #ff8787);
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
```
**Reason**: Pill buttons are trendy decoration, not function.  
**Use Instead**: Rectangular buttons with clear, high-contrast text:
```css
button {
  border-radius: 4px;
  background: #000;
  color: #fff;
  padding: 8px 16px;
  font-weight: 600;
}
```

#### ❌ DON'T: Emoji Icons
```html
<!-- FORBIDDEN -->
<div class="feature">
  🚀 Speed
  <p>Lightning-fast research</p>
</div>

<div class="feature">
  🎯 Accuracy
  <p>Verified results</p>
</div>
```
**Reason**: Emoji are imprecise and childish. They distract from substance.  
**Use Instead**: 
- If visual is needed: Simple icon from icon library (Feather, Material)
- If no visual: Plain text with real descriptions:

```html
<!-- GOOD -->
<div class="feature">
  <h3>Speed</h3>
  <p>Semantic cache reduces research time from 3s to 50ms for similar queries</p>
</div>
```

#### ❌ DON'T: Fake Metrics
```html
<!-- FORBIDDEN -->
<div class="stat">
  <div class="number">99.9%</div>
  <div class="label">Accuracy</div>
  <!-- No data backing this up -->
</div>

<div class="stat">
  <div class="number">1M+</div>
  <div class="label">Queries Processed</div>
  <!-- Completely made up -->
</div>
```
**Reason**: Fake metrics undermine credibility.  
**Use Instead**: Real metrics with source:
```html
<!-- GOOD -->
<div class="stat">
  <div class="number">98.3%</div>
  <div class="label">Tool Success Rate</div>
  <div class="source">From 42 test queries (Sept 2026)</div>
</div>
```

#### ❌ DON'T: Cursor Animation
```css
/* FORBIDDEN */
* {
  cursor: url('custom-cursor.png'), auto;
}

element:hover {
  cursor: grab;
  transition: all 0.3s;
}
```
**Reason**: Custom cursors break accessibility. They're slow and distracting.  
**Use Instead**: Default cursor. Let OS handle it.

#### ❌ DON'T: AI-Generated Images
```html
<!-- FORBIDDEN -->
<img src="ai-generated-chart.png" alt="Generic AI image">
<!-- Stock photo of people staring at graphs -->
```
**Reason**: 
- AI images are obviously fake to trained eyes
- They say "we're marketing-first, substance-second"
- They look generic and placeholder-ish

**Use Instead**: 
- Real screenshots of your actual system
- Data visualizations of real metrics
- Architecture diagrams
- Code examples

#### ❌ DON'T: Em Dashes Everywhere
```
FORBIDDEN:
"Our system is fast—really fast—incredibly fast"
"We believe in quality—in every way—always"
"Research agents—the future—starting today"
```
**Reason**: Overuse of em dashes is lazy writing. It's filler, not substance.

**Use Instead**: Clear, direct sentences:
```
GOOD:
"Cache hit rate: 42.9%. Latency: 50ms vs 3000ms."
"Tool success rate: 98.3%. Recovery rate: 100%."
```

#### ❌ DON'T: "Made with AI" Tag
```html
<!-- FORBIDDEN -->
<footer>
  <p>Made with AI ✨</p>
</footer>
```
**Reason**: It's obvious this is AI-assisted. Saying it explicitly looks insecure.

**Use Instead**: Nothing. Let the work speak. If asked, be honest:
> "This project uses Google's Agent Development Kit for orchestration and sentence-transformers for semantic embeddings."

#### ❌ DON'T: AI Copy
```
FORBIDDEN:
"Harness the power of cutting-edge AI technology"
"Transform your workflow with intelligent automation"
"Experience the future of research"
"Unleash the potential of autonomous agents"
```
**Reason**: This is meaningless buzzword soup. It signals lack of substance.

**Use Instead**: Specific, measurable descriptions:
```
GOOD:
"Semantic cache reduces query time by 60% for related queries.
Query 1: 3000ms. Query 2 (89% similar): 50ms."

"Fault injection tests show 100% recovery rate from:
- Timeouts (retry with exponential backoff)
- Malformed JSON (schema validation + fallback tool)
- Empty results (query reformulation)"
```

---

### DON'T: Sacrifice Quality for Features

#### ❌ DON'T: Commit Untested Code
- Every feature must have tests
- Every test must pass
- Code coverage > 80%
- No exceptions

#### ❌ DON'T: Skip Documentation
- README must be comprehensive
- Architecture must be diagrammed
- Functions must have docstrings
- Design decisions must be explained

#### ❌ DON'T: Hardcode Configuration
- Every tunable parameter goes in config file
- Secrets go in environment variables
- Different configs for dev/test/prod

#### ❌ DON'T: Silent Failures
- Every error must be caught explicitly
- Every failure must be logged
- Every recovery must be traced

---

## SECTION 3: DOS (Engineering Discipline)

### DO: Include Legal/Compliance Pages

#### DO: T&Cs Page
Even for a prototype, have Terms & Conditions:
```markdown
# Terms & Conditions

This is a prototype research agent built for educational purposes.

- No warranty of accuracy
- Results should be verified independently
- API usage subject to rate limits
- Cache entries expire after 24 hours
```

**Why**: Shows you think about responsibility, not just features.

#### DO: Privacy Policy Page
```markdown
# Privacy Policy

This system:
- Does NOT store user queries after execution
- Does NOT track users
- Does NOT sell data
- Uses Redis caching (TTL: 24h)
- Logs are stored locally only
```

**Why**: Builds trust. Shows you respect user data.

#### DO: Custom Domain
If deploying: Use a real domain, not `localhost:8501` or `heroku-app-12345.com`.

Even a free domain (Vercel, GitHub Pages) is better than default.

**Why**: Professional appearance. Signals you took it seriously.

#### DO: Site Favicon
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
```
- A real favicon (not the default browser icon)
- Matches your design system
- At least 32x32 pixels

**Why**: Shows attention to detail.

---

### DO: Professional Presentation

#### DO: README Must Include

```markdown
# Agent-as-Database

## What This Is
[Clear, specific description]

## Quick Start
[3-5 steps to run]

## Architecture
[Diagram or clear text description]

## Usage Examples
[Real example queries and results]

## How It Works
[Explain the components]

## Monitoring
[How to view metrics]

## Testing
[How to run tests]

## Troubleshooting
[Common errors and fixes]

## Performance
[Real metrics from test runs]
```

#### DO: Architecture Diagram
```
[Actual diagram showing data flow]

Components:
- Query Analyzer
- Semantic Cache
- Query Planner
- Task Executor
- Knowledge Graph
- Verifier
- Report Generator
- Trace System
```

#### DO: Sample Execution Transcripts
Show real output:
```
$ python -m src.main query "Compare vLLM and Ollama"

[14:32:00] Starting query analysis...
[14:32:00] Query embedding generated
[14:32:00] Checking semantic cache...
[14:32:00] Cache: MISS
[14:32:00] Generating task plan...

Plan:
  T1: Research vLLM (web_search)
  T2: Research Ollama (web_search)
  T3: Compare (semantic_extract)

[14:32:01] Executing tasks...
[14:32:02] Building knowledge graph...
[14:32:02] Verifying claims...

✓ Query completed in 2.1 seconds
✓ Claims verified: 12/12
✓ Confidence: 94%

Report saved to: outputs/reports/Q-0042.json
```

---

## SECTION 4: Vibe vs. Substance

### What Vibe-Coded Looks Like

```html
<section class="hero">
  <h1>The Future of AI</h1>
  <!-- Purple gradient, emoji, animation -->
</section>

<section class="features">
  <div>🚀 Fast</div>
  <div>🎯 Accurate</div>
  <div>🔥 Powerful</div>
  <!-- No actual numbers -->
</section>

<section class="testimonials">
  ★★★★★ "Changed my life!" - Anonymous User
  <!-- Made up reviews -->
</section>

<footer>
  <p>Made with AI ✨</p>
</footer>
```

### What Professional Looks Like

```html
<section class="overview">
  <h1>Agent-as-Database</h1>
  <p>Semantic knowledge graph query engine with TTL-based caching and 
     observable failure recovery.</p>
</section>

<section class="metrics">
  <div>
    <strong>42.9%</strong>
    <span>Cache hit rate after 50 queries</span>
  </div>
  <div>
    <strong>1.3 seconds</strong>
    <span>Avg latency on partial cache hits (60% time saved)</span>
  </div>
  <div>
    <strong>98.3%</strong>
    <span>Tool success rate (4 tools × 50 queries)</span>
  </div>
</section>

<section class="architecture">
  <img src="architecture-diagram.svg" alt="System architecture">
  <p>Knowledge graph → Query Analyzer → Cache Lookup → Planner → 
     Executor → Verifier → Report Generator</p>
</section>

<section class="documentation">
  <a href="/README.md">Full README with setup instructions</a>
  <a href="/docs/architecture.md">Architecture documentation</a>
  <a href="/examples/">Sample execution transcripts</a>
</section>

<footer>
  <p>Built by Ankit Sharma | September 2026</p>
</footer>
```

**The Difference**:
- First: Tries to impress with style
- Second: Impresses with substance

---

## SECTION 5: Checklist

### Before Final Submission

- [ ] All code has type hints
- [ ] All functions have docstrings
- [ ] Test coverage > 80%
- [ ] All tests passing
- [ ] No hardcoded values
- [ ] No fake metrics
- [ ] No emoji in UI (except carefully chosen icons)
- [ ] No gradients in dashboard
- [ ] No fake testimonials
- [ ] README is comprehensive
- [ ] Architecture diagram exists
- [ ] 3 sample execution transcripts
- [ ] Real metrics reported
- [ ] Privacy policy included
- [ ] T&Cs included
- [ ] Custom favicon included
- [ ] Domain or professional URL (not localhost)
- [ ] Code is modular and testable
- [ ] Errors are handled explicitly
- [ ] Failures are logged
- [ ] All decisions are traced
- [ ] No "made with AI" tag
- [ ] No vague hero text
- [ ] No AI-generated images

---

## SECTION 6: The Right Mindset

> "If you have to explain how great your product is, it's not great."

Your code and metrics should speak for themselves. If you find yourself writing marketing copy, you're compensating for lack of substance.

**Good Engineering**:
- Clear architecture
- Comprehensive testing
- Observable behavior
- Real metrics
- Honest documentation

**Marketing Spin**:
- Vague claims
- Fake testimonials
- Visual noise
- Unverifiable numbers
- "AI-powered" everywhere

**Choose good engineering.**

---

## SECTION 7: Final Note

This project will be reviewed by engineers who value **judgment** and **quality** over feature count.

Every design decision should be defensible:
- Why this architecture?
- Why semantic caching?
- Why these metrics?
- Why this tool selection?

**Your answer should never be**: "Because it sounds cool" or "Because it looks good."

**Your answer should always be**: "Because it solves a real problem better than alternatives."

---

**Document Version**: 1.0  
**Last Updated**: September 24, 2026  
**Status**: Binding for all code and documentation
