import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Agent-as-Database Monitoring", page_icon="🧠", layout="wide")

st.title("🧠 Agent-as-Database Monitoring Dashboard")
st.markdown("Monitor semantic cache performance, tool success rates, and knowledge graph statistics.")

def load_reports():
    reports_dir = os.path.join(os.path.dirname(__file__), '../../outputs/reports')
    reports = []
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json'):
                with open(os.path.join(reports_dir, filename), 'r') as f:
                    reports.append(json.load(f))
    return reports

reports = load_reports()

if not reports:
    st.warning("No query reports found. Run some queries using the CLI first!")
else:
    # Key Metrics
    total_queries = len(reports)
    cache_hits = sum(1 for r in reports if r.get('execution_summary', {}).get('cache_hit_type') in ['full', 'partial'])
    hit_rate = (cache_hits / total_queries) * 100 if total_queries > 0 else 0
    avg_latency = sum(r.get('execution_summary', {}).get('total_duration_ms', 0) for r in reports) / total_queries
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Queries", total_queries)
    col2.metric("Cache Hit Rate", f"{hit_rate:.1f}%")
    col3.metric("Avg Latency", f"{avg_latency:.0f} ms")
    col4.metric("Avg Freshness Score", f"{sum(r.get('freshness_score', 0) for r in reports) / total_queries:.2f}")

    st.markdown("---")
    
    # Query History
    st.subheader("Query History")
    for report in reversed(reports):
        with st.expander(f"Query: {report.get('query', 'Unknown')} ({report.get('query_id')})"):
            st.json(report)
