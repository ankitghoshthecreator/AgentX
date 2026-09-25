import json
import logging
import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates structured JSON and human-readable Markdown reports."""
    
    def generate_json_report(
        self,
        query_id: str,
        original_query: str,
        claims: list,
        execution_summary: dict,
        planning_trace: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate JSON report with embedded planning trace for full observability."""
        report = {
            "query_id": query_id,
            "query": original_query,
            "planning_trace": planning_trace or [],
            "execution_summary": execution_summary,
            "claims": claims,
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "freshness_score": 0.95
        }
        logger.info(f"Generated JSON report for query {query_id}")
        return report

    def generate_markdown_report(self, json_report: Dict[str, Any]) -> str:
        """Convert JSON report into readable Markdown."""
        lines = []
        lines.append(f"# Query Report: {json_report['query']}")
        lines.append(f"\n**Query ID**: {json_report['query_id']}")

        exec_time = json_report['execution_summary'].get('total_duration_ms', 0) / 1000.0
        lines.append(f"**Execution Time**: {exec_time:.2f} seconds")
        hit_type = json_report['execution_summary'].get('cache_hit_type', 'miss')
        lines.append(f"**Cache Hit**: {hit_type.capitalize()}")

        if json_report.get("planning_trace"):
            lines.append("\n## Planning Trace")
            for step in json_report["planning_trace"]:
                lines.append(
                    f"- [{step['task_id']}] {step['description']} "
                    f"-> tool=`{step['tool']}` deps={step.get('dependencies', [])}"
                )

        lines.append("\n## Claims / Evidence")
        for claim in json_report['claims']:
            marker = "VERIFIED" if claim['status'] == 'verified' else "UNVERIFIED"
            lines.append(f"- [{marker}] {claim['text']} (Confidence: {claim['confidence']*100:.1f}%)")

        return "\n".join(lines)
