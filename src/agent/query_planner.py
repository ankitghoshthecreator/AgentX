import uuid
import logging
from typing import List, Dict
from .types import QueryRepresentation, Task, TaskDAG

logger = logging.getLogger(__name__)

class QueryPlanner:
    """Decomposes queries into executable task DAGs."""
    
    def __init__(self):
        logger.info("QueryPlanner initialized.")

    def plan(self, query: QueryRepresentation) -> TaskDAG:
        """Create a task DAG based on extracted entities and relationships."""
        plan_id = f"PLAN-{uuid.uuid4().hex[:4].upper()}"
        tasks = []
        
        # Simple heuristic planning based on entities
        for idx, entity in enumerate(query.entities):
            # We assign a research task for each entity identified
            if entity.type in ["framework", "hardware", "concept"]:
                tasks.append(
                    Task(
                        task_id=f"T{idx+1}",
                        description=f"Research {entity.name} capabilities",
                        tool="web_search",
                        inputs={"query": f"{entity.name} {entity.type} capabilities documentation"},
                        priority=1
                    )
                )
        
        # Add a synthesis/extraction task if there are multiple entities to compare
        if len(tasks) > 1:
            tasks.append(
                Task(
                    task_id=f"T{len(tasks)+1}",
                    description="Extract and compare information across researched entities",
                    tool="semantic_extract",
                    inputs={"entities": [e.name for e in query.entities]},
                    priority=2,
                    dependencies=[t.task_id for t in tasks]
                )
            )
            
        # Fallback if no entities were found
        if not tasks:
            tasks.append(
                Task(
                    task_id="T1",
                    description=f"Research general query: {query.original_text}",
                    tool="web_search",
                    inputs={"query": query.original_text},
                    priority=1
                )
            )
            
        dag = TaskDAG(
            plan_id=plan_id,
            tasks=tasks,
            total_estimated_time_ms=sum(t.estimated_time_ms for t in tasks),
            parallelizable_tasks=len([t for t in tasks if not t.dependencies]),
            critical_path=[t.task_id for t in tasks if t.dependencies]
        )
        
        logger.debug(f"Generated task plan {plan_id} with {len(tasks)} tasks.")
        return dag
