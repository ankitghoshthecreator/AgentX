import uuid
import logging
from typing import List, Dict
from .types import QueryRepresentation, Task, TaskDAG

logger = logging.getLogger(__name__)

class QueryPlanner:
    """Decomposes queries into executable task DAGs with multi-source research strategy."""

    def __init__(self):
        logger.info("QueryPlanner initialized.")

    def plan(self, query: QueryRepresentation) -> TaskDAG:
        plan_id = f"PLAN-{uuid.uuid4().hex[:4].upper()}"
        tasks = []

        for idx, entity in enumerate(query.entities):
            if entity.type in ["framework", "hardware", "concept"]:
                # Task 1: Primary research via Wikipedia
                wiki_task_id = f"T{len(tasks)+1}"
                tasks.append(Task(
                    task_id=wiki_task_id,
                    description=f"Wikipedia: research {entity.name}",
                    tool="web_search",
                    fallback_tool="duckduckgo_search",
                    inputs={"query": f"{entity.name} {entity.type} capabilities"},
                    priority=1,
                    estimated_time_ms=800
                ))
                # Task 2: Cross-reference via DuckDuckGo (parallel, no dependency on wiki)
                ddg_task_id = f"T{len(tasks)+1}"
                tasks.append(Task(
                    task_id=ddg_task_id,
                    description=f"DuckDuckGo: cross-reference {entity.name}",
                    tool="duckduckgo_search",
                    fallback_tool="web_search",
                    inputs={"query": f"{entity.name} overview features"},
                    priority=1,
                    estimated_time_ms=600
                ))

        # Synthesis: only if we have at least 2 tasks to synthesize
        if len(tasks) >= 2:
            tasks.append(Task(
                task_id=f"T{len(tasks)+1}",
                description="Synthesize and cross-validate multi-source evidence",
                tool="semantic_extract",
                inputs={"entities": [e.name for e in query.entities]},
                priority=2,
                dependencies=[t.task_id for t in tasks],
                estimated_time_ms=300
            ))

        # Fallback: no entities found
        if not tasks:
            tasks.append(Task(
                task_id="T1",
                description=f"General research: {query.original_text}",
                tool="web_search",
                fallback_tool="duckduckgo_search",
                inputs={"query": query.original_text},
                priority=1,
                estimated_time_ms=800
            ))

        dag = TaskDAG(
            plan_id=plan_id,
            tasks=tasks,
            total_estimated_time_ms=sum(t.estimated_time_ms for t in tasks),
            parallelizable_tasks=len([t for t in tasks if not t.dependencies]),
            critical_path=[t.task_id for t in tasks if t.dependencies]
        )
        logger.info(
            f"Plan {plan_id}: {len(tasks)} tasks, "
            f"{dag.parallelizable_tasks} parallelizable, "
            f"critical_path={dag.critical_path}"
        )
        return dag
