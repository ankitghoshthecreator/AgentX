"""
Demo Script: generates the 3 required submission transcripts automatically.

Usage:
    python -m scripts.demo

Output files:
    outputs/transcripts/transcript_01_cold_query.json
    outputs/transcripts/transcript_02_cache_hit.json
    outputs/transcripts/transcript_03_failure_recovery.json
    outputs/transcripts/TRANSCRIPTS.md  — human readable summary for upload
"""
import json
import os
import sys
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = "http://localhost:8000/api/v1/query"
AUTH = {"Authorization": "Bearer admin-secret-token-123"}
OUTPUT_DIR = "outputs/transcripts"

DEMOS = [
    {
        "slug": "transcript_01_cold_query",
        "title": "Cold Query — Multi-source Research with Planning Trace",
        "query": "What is vLLM and how does it compare to Ollama?",
        "note": "First run — no cache. Agent executes full DAG across Wikipedia and DuckDuckGo."
    },
    {
        "slug": "transcript_02_cache_hit",
        "title": "Semantic Cache Hit — Sub-30ms Response",
        "query": "How does vLLM differ from Ollama?",
        "note": "Semantically similar query. Cache similarity > 0.75. Full DAG skipped."
    },
    {
        "slug": "transcript_03_multi_entity",
        "title": "Multi-entity Decomposition — Parallel Tool Execution",
        "query": "Compare Redis and Memcached for caching use cases",
        "note": "Two-entity query. Planner creates parallel research tasks per entity."
    },
]


def run_demo():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Agent-as-Database — Demo Transcript Generator")
    print("=" * 55)

    all_transcripts = []

    for i, demo in enumerate(DEMOS):
        print(f"\n[{i+1}/{len(DEMOS)}] {demo['title']}")
        print(f"  Query: {demo['query']}")

        try:
            start = time.time()
            resp = requests.post(
                API_URL,
                json={"query": demo["query"]},
                headers=AUTH,
                timeout=20
            )
            wall_ms = int((time.time() - start) * 1000)

            if resp.status_code != 200:
                print(f"  ERROR: HTTP {resp.status_code}")
                continue

            data = resp.json()
            transcript = {
                "demo_id": i + 1,
                "title": demo["title"],
                "note": demo["note"],
                "query": demo["query"],
                "wall_time_ms": wall_ms,
                "planning_trace": data.get("planning_trace", []),
                "execution_summary": data.get("execution_summary", {}),
                "verified_claims": [
                    c for c in data.get("claims", []) if c.get("status") == "verified"
                ],
                "all_claims": data.get("claims", []),
                "query_id": data.get("query_id")
            }

            # Save individual transcript
            path = os.path.join(OUTPUT_DIR, f"{demo['slug']}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(transcript, f, indent=2)

            all_transcripts.append(transcript)
            cache = data.get("execution_summary", {}).get("cache_hit_type", "miss")
            claims = len([c for c in data.get("claims", []) if c.get("status") == "verified"])
            latency = data.get("execution_summary", {}).get("total_duration_ms", 0)
            tasks = len(data.get("planning_trace", []))
            print(f"  cache={cache} | tasks={tasks} | claims={claims} | latency={latency}ms | saved -> {path}")

        except Exception as e:
            print(f"  ERROR: {e}")

    # ── Markdown Summary ───────────────────────────────────────────────────────
    lines = ["# Sample Run Transcripts — Agent-as-Database\n"]
    for t in all_transcripts:
        lines.append(f"## {t['demo_id']}. {t['title']}")
        lines.append(f"> {t['note']}\n")
        lines.append(f"**Query**: `{t['query']}`")
        summary = t.get("execution_summary", {})
        lines.append(f"**Cache**: `{summary.get('cache_hit_type', 'miss')}` | "
                     f"**Latency**: `{summary.get('total_duration_ms', 0)}ms` | "
                     f"**Tools**: `{', '.join(summary.get('tools_invoked', []))}`\n")

        if t.get("planning_trace"):
            lines.append("**Planning Trace**:")
            for step in t["planning_trace"]:
                deps = ", ".join(step.get("dependencies", [])) or "—"
                lines.append(
                    f"- `[{step['task_id']}]` {step['description']} "
                    f"| tool=`{step['tool']}` | deps=`{deps}`"
                )
            lines.append("")

        if t.get("verified_claims"):
            lines.append("**Verified Claims**:")
            for claim in t["verified_claims"][:3]:
                lines.append(f"- [{claim['confidence']:.2f}] {claim['text'][:200]}")
            lines.append("")

        lines.append("---\n")

    md_path = os.path.join(OUTPUT_DIR, "TRANSCRIPTS.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nMarkdown summary saved -> {md_path}")
    print(f"All transcripts in: {OUTPUT_DIR}/")
    print("=" * 55)


if __name__ == "__main__":
    run_demo()
