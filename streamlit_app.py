"""
Streamlit Cloud entry point.
Standalone mode — imports the orchestrator directly (no separate API server needed).
"""
import streamlit as st
import json
import os
import sys

# Add project root to path so src.* imports work on Streamlit Cloud
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Agent-as-Database | Ops Console", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'JetBrains Mono', 'Courier New', monospace; font-size: 13px; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    [data-testid="metric-container"] {
        background: #f7f7f7; border: 1px solid #ddd;
        border-radius: 3px; padding: 0.5rem 1rem;
    }
    h2, h3 { font-size: 13px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #333; }
    .trace-box {
        background: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 11.5px;
        padding: 0.8rem; border-radius: 3px; white-space: pre-wrap;
        max-height: 300px; overflow-y: auto;
    }
    .pill-verified { background:#e6f4ea; color:#137333; border-radius:3px; padding:1px 6px; font-size:11px; font-weight:600; }
    .pill-unverified { background:#fce8e6; color:#c5221f; border-radius:3px; padding:1px 6px; font-size:11px; font-weight:600; }
    .pill-full { background:#e8f0fe; color:#1a73e8; border-radius:3px; padding:1px 6px; font-size:11px; font-weight:600; }
    .pill-miss { background:#f1f3f4; color:#555; border-radius:3px; padding:1px 6px; font-size:11px; font-weight:600; }
    .plan-step { border-left:3px solid #ccc; padding-left:8px; margin-bottom:4px; font-size:12px; font-family:monospace; }
    .plan-step-tool { color:#1a73e8; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Load cached reports from disk ─────────────────────────────────────────────
def load_reports():
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs', 'reports')
    reports = []
    if os.path.exists(reports_dir):
        for filename in sorted(os.listdir(reports_dir), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(reports_dir, filename), 'r', encoding='utf-8') as f:
                    try:
                        reports.append(json.load(f))
                    except Exception:
                        pass
    return reports

reports = load_reports()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## Agent-as-Database / Ops Console")
st.markdown("---")

# ── System Metrics ─────────────────────────────────────────────────────────────
total = len(reports)
hits = sum(1 for r in reports if r.get('execution_summary', {}).get('cache_hit_type') in ['full', 'partial'])
hit_rate = (hits / total * 100) if total else 0
avg_latency = sum(r.get('execution_summary', {}).get('total_duration_ms', 0) for r in reports) / max(total, 1)
tools_seen = set(t for r in reports for t in r.get('execution_summary', {}).get('tools_invoked', []))

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Queries Processed", total)
c2.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
c3.metric("Avg Latency (ms)", f"{avg_latency:.0f}")
c4.metric("Cache Misses", total - hits)
c5.metric("Tools Active", len(tools_seen) if tools_seen else "—")

st.markdown("---")

# ── Session state ─────────────────────────────────────────────────────────────
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None

# ── Lazy-load orchestrator (heavy — spacy + sentence-transformers) ─────────────
@st.cache_resource(show_spinner="Loading Agent models (first run ~30s)...")
def get_orchestrator():
    from src.agent.orchestrator import AgentOrchestrator
    return AgentOrchestrator()

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown("### Query Executor")
    query_input = st.text_area(
        label="goal",
        label_visibility="collapsed",
        height=72,
        placeholder="Natural language goal — e.g. Compare Redis and Memcached for caching"
    )
    run = st.button("Execute Agent", use_container_width=True)

    if run and query_input.strip():
        with st.spinner("Loading models and executing DAG..."):
            try:
                orchestrator = get_orchestrator()
                result = orchestrator.process_query(query_input.strip())
                st.session_state.last_result = result
                # Reload reports after new execution
                reports.clear()
                reports.extend(load_reports())
                st.rerun()
            except Exception as e:
                st.error(f"Execution error: {e}")

    result = st.session_state.last_result
    if result:
        summary = result.get("execution_summary", {})
        cache_type = summary.get("cache_hit_type", "miss")
        dur = summary.get("total_duration_ms", 0)
        tools_used = summary.get("tools_invoked", [])
        tasks_ok = summary.get("tasks_executed", 0)
        tasks_fail = summary.get("tasks_failed", 0)

        st.markdown("**Execution Summary**")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Duration", f"{dur} ms")
        s2.metric("Cache", cache_type.upper())
        s3.metric("Tasks OK", tasks_ok)
        s4.metric("Failures", tasks_fail)
        if tools_used:
            st.markdown(f"Tools invoked: `{'`, `'.join(tools_used)}`")

        trace = result.get("planning_trace", [])
        if trace:
            st.markdown("**Planning Trace**")
            for step in trace:
                deps = ", ".join(step.get("dependencies", [])) or "none"
                st.markdown(
                    f'<div class="plan-step"><b>[{step["task_id"]}]</b> {step["description"]}<br>'
                    f'tool=<span class="plan-step-tool">{step["tool"]}</span> &nbsp; deps=<code>{deps}</code></div>',
                    unsafe_allow_html=True
                )

        claims = result.get("claims", [])
        if claims:
            st.markdown("**Verified Claims**")
            for claim in claims:
                text = claim.get("text", "")[:300]
                conf = claim.get("confidence", 0)
                status = claim.get("status", "unverified")
                pill = "pill-verified" if status == "verified" else "pill-unverified"
                st.markdown(
                    f'<div style="border-bottom:1px solid #eee;padding:5px 0;font-size:12px;">'
                    f'<span class="{pill}">{status.upper()}</span> '
                    f'<span style="color:#888">conf={conf:.2f}</span><br>{text}</div>',
                    unsafe_allow_html=True
                )

with right:
    st.markdown("### Raw Execution Trace")
    trace_text = json.dumps(result, indent=2) if result else "No execution yet."
    st.markdown(f'<div class="trace-box">{trace_text}</div>', unsafe_allow_html=True)

    st.markdown("### Knowledge Graph")
    if reports:
        try:
            import networkx as nx
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            G = nx.DiGraph()
            for r in reports:
                for step in r.get("planning_trace", []):
                    G.add_node(step["task_id"], label=step.get("tool", ""))
                    for dep in step.get("dependencies", []):
                        G.add_edge(dep, step["task_id"])
            if G.number_of_nodes() > 0:
                fig, ax = plt.subplots(figsize=(5, 3))
                pos = nx.spring_layout(G, seed=42)
                nx.draw_networkx(G, pos, ax=ax, node_color="#d4e8ff", node_size=800,
                                 font_size=8, arrows=True, edge_color="#aaa", font_family="monospace")
                ax.set_axis_off()
                fig.patch.set_facecolor("#f7f7f7")
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            else:
                st.caption("Graph will populate after first non-cached query.")
        except Exception as e:
            st.caption(f"Graph render unavailable: {e}")

    st.markdown("### Query Log")
    for r in reports[:6]:
        qid = r.get("query_id", "—")
        query = r.get("query", "—")[:55]
        cache = r.get("execution_summary", {}).get("cache_hit_type", "miss")
        dur = r.get("execution_summary", {}).get("total_duration_ms", 0)
        task_count = len(r.get("planning_trace", []))
        pill = "pill-full" if cache == "full" else ("pill-verified" if cache == "partial" else "pill-miss")
        st.markdown(
            f'<div style="border-bottom:1px solid #eee;padding:5px 0;font-size:12px;">'
            f'<code style="color:#888">{qid}</code>&nbsp;<span class="{pill}">{cache.upper()}</span>&nbsp;'
            f'<span style="color:#555">{dur}ms</span>&nbsp;<span style="color:#aaa">{task_count} tasks</span><br>'
            f'<span>{query}</span></div>',
            unsafe_allow_html=True
        )
