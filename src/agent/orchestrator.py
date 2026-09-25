import time
import json
import os
import logging
from typing import Dict, Any

from .query_analyzer import QueryAnalyzer
from .query_planner import QueryPlanner
from .tool_selector import ToolSelector
from ..cache.semantic_cache import SemanticCache
from ..execution.task_executor import TaskExecutor
from ..graph.graph_builder import GraphBuilder
from ..verification.verifier import ClaimVerifier
from ..output.report_generator import ReportGenerator
from ..monitoring.tracer import Tracer

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.tracer = Tracer()
        self.analyzer = QueryAnalyzer()
        self.cache = SemanticCache(similarity_threshold=0.75)
        self.planner = QueryPlanner()
        self.tool_selector = ToolSelector()
        self.executor = TaskExecutor()
        self.graph = GraphBuilder()
        self.verifier = ClaimVerifier()
        self.reporter = ReportGenerator()
        logger.info("AgentOrchestrator initialized with Phase 3 Multi-tenant architecture.")

    def process_query(self, query_text: str, tenant_id: str = "default_tenant") -> Dict[str, Any]:
        start_time = time.time()

        # 1. Analyze
        query_rep = self.analyzer.analyze(query_text)
        self.tracer.record_event(query_rep.query_id, "query_analysis", {
            "entities": [e.name for e in query_rep.entities]
        })

        # 2. Check semantic cache (tenant-scoped)
        cache_result = None
        if query_rep.embedding:
            cache_result = self.cache.lookup(tenant_id, query_rep.embedding)

        if cache_result and cache_result.hit_type == "full":
            self.tracer.record_event(query_rep.query_id, "cache_lookup", {
                "result": "full", "tenant_id": tenant_id
            })
            execution_summary = {
                "total_duration_ms": int((time.time() - start_time) * 1000),
                "cache_hit_type": "full",
                "tenant_id": tenant_id
            }
            cached_claims = cache_result.cached_subgraph.get("claims", [])
            if not cached_claims:
                cached_claims = self.verifier.verify_claims({
                    "cache": {"results": "Cached result recovered from semantic cache"}
                })
            cached_trace = cache_result.cached_subgraph.get("planning_trace", [])
            report = self.reporter.generate_json_report(
                query_rep.query_id, query_text, cached_claims, execution_summary,
                planning_trace=cached_trace
            )
            return report

        self.tracer.record_event(query_rep.query_id, "cache_lookup", {
            "result": "miss" if not cache_result else "partial", "tenant_id": tenant_id
        })

        # 3. Plan — build the DAG and log the full planning trace
        plan = self.planner.plan(query_rep)
        planning_trace = [
            {
                "task_id": t.task_id,
                "description": t.description,
                "tool": t.tool,
                "dependencies": t.dependencies,
                "estimated_time_ms": t.estimated_time_ms,
                "priority": t.priority
            }
            for t in plan.tasks
        ]
        logger.info(f"Planning trace for {query_rep.query_id}: {json.dumps(planning_trace, indent=2)}")
        self.tracer.record_event(query_rep.query_id, "planning", {
            "plan_id": plan.plan_id,
            "task_count": len(plan.tasks),
            "parallelizable": plan.parallelizable_tasks
        })

        # 4. Tool selection
        self.tool_selector.select_tools(query_rep.embedding)

        # 5. Execute DAG
        execution_results = self.executor.execute_plan(plan)

        # 6. Update knowledge graph (tenant-scoped)
        for task_id, res in execution_results.items():
            if "error" not in res:
                source = res.get("source", task_id)
                self.graph.add_node(tenant_id, f"task_{task_id}", {
                    "source": source,
                    "result_preview": str(res)[:80]
                })

        # 7. Verify claims
        claims = self.verifier.verify_claims(execution_results)

        # 8. Store in semantic cache with claims and trace
        if query_rep.embedding:
            self.cache.store(
                tenant_id, query_rep.query_id, query_rep.embedding,
                {"claims": claims, "planning_trace": planning_trace}
            )

        # 9. Build and persist report
        execution_summary = {
            "total_duration_ms": int((time.time() - start_time) * 1000),
            "cache_hit_type": "miss" if not cache_result else "partial",
            "tenant_id": tenant_id,
            "tools_invoked": list({t.tool for t in plan.tasks}),
            "tasks_executed": len(execution_results),
            "tasks_failed": sum(1 for r in execution_results.values() if "error" in r)
        }

        report = self.reporter.generate_json_report(
            query_rep.query_id, query_text, claims, execution_summary,
            planning_trace=planning_trace
        )

        os.makedirs("outputs/reports", exist_ok=True)
        with open(f"outputs/reports/{query_rep.query_id}.json", "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved: outputs/reports/{query_rep.query_id}.json")

        return report
