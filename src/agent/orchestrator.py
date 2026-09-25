import time
import logging
from typing import Dict, Any
import os
import json

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
        logger.info("AgentOrchestrator fully initialized.")

    def process_query(self, query_text: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Analyze
        query_rep = self.analyzer.analyze(query_text)
        self.tracer.record_event(query_rep.query_id, "query_analysis", {"entities": len(query_rep.entities)})
        
        # 2. Check Cache
        cache_result = None
        if query_rep.embedding:
            cache_result = self.cache.lookup(query_rep.embedding)
            
        if cache_result and cache_result.hit_type == "full":
            self.tracer.record_event(query_rep.query_id, "cache_lookup", {"result": "full"})
            logger.info("Full cache hit!")
            execution_summary = {
                "total_duration_ms": int((time.time() - start_time) * 1000),
                "cache_hit_type": "full"
            }
            # Fast path
            claims = self.verifier.verify_claims({"cache": {"results": "Cached result recovered from semantic cache"}})
            
            # Print Markdown for CLI
            report = self.reporter.generate_json_report(query_rep.query_id, query_text, claims, execution_summary)
            print(self.reporter.generate_markdown_report(report))
            return report

        self.tracer.record_event(query_rep.query_id, "cache_lookup", {"result": "miss" if not cache_result else "partial"})
        
        # 3. Plan
        plan = self.planner.plan(query_rep)
        self.tracer.record_event(query_rep.query_id, "planning", {"tasks": len(plan.tasks)})
        
        # 4. Tool Selection
        tools_to_use = self.tool_selector.select_tools(query_rep.embedding)
        
        # 5. Execute
        execution_results = self.executor.execute_plan(plan)
        self.tracer.record_event(query_rep.query_id, "execution", {"tasks_completed": len(execution_results)})
        
        # 6. Graph building
        for task_id, res in execution_results.items():
            if "error" not in res:
                self.graph.add_node(f"task_{task_id}", {"result": str(res)[:50]})
                
        # 7. Verification
        claims = self.verifier.verify_claims(execution_results)
        
        # 8. Cache result
        if query_rep.embedding:
            self.cache.store(query_rep.query_id, query_rep.embedding, {"nodes": [], "edges": []})
            
        # 9. Report
        execution_summary = {
            "total_duration_ms": int((time.time() - start_time) * 1000),
            "cache_hit_type": "miss" if not cache_result else "partial"
        }
        report = self.reporter.generate_json_report(query_rep.query_id, query_text, claims, execution_summary)
        
        logger.info(f"Query {query_rep.query_id} processed in {execution_summary['total_duration_ms']}ms")
        
        # Print Markdown for CLI
        print("\n" + "="*50)
        print(self.reporter.generate_markdown_report(report))
        print("="*50 + "\n")
        
        # Save output
        os.makedirs("outputs/reports", exist_ok=True)
        with open(f"outputs/reports/{query_rep.query_id}.json", "w") as f:
            json.dump(report, f, indent=2)
            
        return report
