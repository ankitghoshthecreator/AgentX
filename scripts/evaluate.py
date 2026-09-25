"""
Evaluation Harness: measures claim quality against known-answer test queries.

Usage:
    python -m scripts.evaluate

Outputs:
    outputs/evaluation/eval_report.json  — machine-readable results
    outputs/evaluation/eval_report.md    — human-readable summary
"""
import json
import os
import sys
import time
import requests
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = "http://localhost:8000/api/v1/query"
AUTH_HEADER = {"Authorization": "Bearer admin-secret-token-123"}

# ── Test Cases ─────────────────────────────────────────────────────────────────
# Each test case has a query and a list of keywords that MUST appear in at least
# one verified claim for the test to pass (precision signal).
TEST_CASES: List[Dict[str, Any]] = [
    {
        "query": "What is Python programming language?",
        "required_keywords": ["python", "programming", "language"],
        "forbidden_keywords": [],
        "description": "Basic factual lookup — Python"
    },
    {
        "query": "What is a REST API?",
        "required_keywords": ["api", "http", "request"],
        "forbidden_keywords": [],
        "description": "Technical concept lookup — REST API"
    },
    {
        "query": "What is machine learning?",
        "required_keywords": ["machine", "learning", "data"],
        "forbidden_keywords": [],
        "description": "Domain concept — Machine Learning"
    },
    {
        "query": "What is Redis used for?",
        "required_keywords": ["redis", "cache", "data"],
        "forbidden_keywords": [],
        "description": "Specific technology — Redis"
    },
    {
        "query": "What is Docker?",
        "required_keywords": ["container", "docker", "software"],
        "forbidden_keywords": [],
        "description": "Specific technology — Docker"
    },
]


def evaluate_response(response: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single response against required/forbidden keyword criteria."""
    claims = response.get("claims", [])
    verified_claims = [c for c in claims if c.get("status") == "verified"]
    all_claim_text = " ".join(c.get("text", "").lower() for c in verified_claims)

    required = test_case["required_keywords"]
    forbidden = test_case.get("forbidden_keywords", [])

    keywords_found = [kw for kw in required if kw.lower() in all_claim_text]
    keywords_missing = [kw for kw in required if kw.lower() not in all_claim_text]
    forbidden_found = [kw for kw in forbidden if kw.lower() in all_claim_text]

    precision = len(keywords_found) / len(required) if required else 1.0
    passed = len(keywords_missing) == 0 and len(forbidden_found) == 0

    return {
        "description": test_case["description"],
        "query": test_case["query"],
        "passed": passed,
        "precision": round(precision, 3),
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "forbidden_triggered": forbidden_found,
        "verified_claim_count": len(verified_claims),
        "total_claim_count": len(claims),
        "cache_hit_type": response.get("execution_summary", {}).get("cache_hit_type", "miss"),
        "latency_ms": response.get("execution_summary", {}).get("total_duration_ms", 0),
        "avg_confidence": round(
            sum(c.get("confidence", 0) for c in verified_claims) / max(len(verified_claims), 1), 3
        )
    }


def run_evaluation():
    print("=" * 60)
    print("Agent-as-Database — Evaluation Harness")
    print("=" * 60)

    results = []
    for i, test in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] {test['description']}")
        print(f"  Query: {test['query']}")
        try:
            start = time.time()
            resp = requests.post(API_URL, json={"query": test["query"]}, headers=AUTH_HEADER, timeout=15)
            elapsed = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                result = evaluate_response(resp.json(), test)
                result["wall_time_ms"] = elapsed
                results.append(result)
                status = "PASS" if result["passed"] else "FAIL"
                print(f"  [{status}] precision={result['precision']:.2f} "
                      f"claims={result['verified_claim_count']} "
                      f"cache={result['cache_hit_type']} "
                      f"latency={result['latency_ms']}ms")
            else:
                print(f"  [ERROR] HTTP {resp.status_code}")
                results.append({"description": test["description"], "passed": False, "error": f"HTTP {resp.status_code}"})
        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append({"description": test["description"], "passed": False, "error": str(e)})

    # ── Summary ────────────────────────────────────────────────────────────────
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    avg_precision = sum(r.get("precision", 0) for r in results) / max(total, 1)
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / max(total, 1)

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} passed")
    print(f"Avg Precision: {avg_precision:.3f}")
    print(f"Avg Latency: {avg_latency:.0f}ms")
    print("=" * 60)

    eval_report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / max(total, 1), 3),
            "avg_precision": round(avg_precision, 3),
            "avg_latency_ms": round(avg_latency, 1)
        },
        "test_results": results
    }

    # ── Persist ────────────────────────────────────────────────────────────────
    os.makedirs("outputs/evaluation", exist_ok=True)
    with open("outputs/evaluation/eval_report.json", "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    md_lines = [
        "# Evaluation Report — Agent-as-Database\n",
        f"**Pass Rate**: {passed}/{total} ({eval_report['summary']['pass_rate']*100:.0f}%)",
        f"**Avg Precision**: {avg_precision:.3f}",
        f"**Avg Latency**: {avg_latency:.0f}ms\n",
        "## Test Results\n",
        "| Test | Pass | Precision | Claims | Cache | Latency |",
        "|---|---|---|---|---|---|"
    ]
    for r in results:
        mark = "PASS" if r.get("passed") else "FAIL"
        md_lines.append(
            f"| {r.get('description', '—')} | {mark} | "
            f"{r.get('precision', 0):.2f} | {r.get('verified_claim_count', 0)} | "
            f"{r.get('cache_hit_type', '—')} | {r.get('latency_ms', 0)}ms |"
        )
    with open("outputs/evaluation/eval_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("\nReports saved to outputs/evaluation/")
    return eval_report


if __name__ == "__main__":
    run_evaluation()
