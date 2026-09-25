import time
import logging
from typing import Dict, Any
from ..agent.types import TaskDAG, Task

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Executes tasks with timeout, retry logic, and fallback capabilities."""
    
    def __init__(self):
        self.tools = {
            "web_search": self._mock_web_search,
            "github_api": self._mock_github_api,
            "semantic_extract": self._mock_semantic_extract
        }
        logger.info("TaskExecutor initialized with available tools.")

    def _mock_web_search(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock web search tool execution."""
        time.sleep(1) # simulate network call
        return {"results": [f"Mock search result for {inputs.get('query')}"]}
        
    def _mock_github_api(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock github API tool execution."""
        time.sleep(0.5)
        return {"stars": 1000, "description": f"Mock repo data for {inputs.get('query')}"}

    def _mock_semantic_extract(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Mock semantic extraction tool execution."""
        time.sleep(0.5)
        return {"extracted": f"Mock extracted capabilities for {inputs.get('entities')}"}

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task with retries."""
        logger.info(f"Executing task {task.task_id}: {task.description} using '{task.tool}'")
        
        if task.tool not in self.tools:
            logger.warning(f"Tool '{task.tool}' not found.")
            if task.fallback_tool and task.fallback_tool in self.tools:
                logger.info(f"Using fallback tool '{task.fallback_tool}' for task {task.task_id}")
                task.tool = task.fallback_tool
            else:
                return {"error": f"Tool '{task.tool}' missing and no fallback available"}
            
        try:
            # Execute tool (in production, run in async loop or separate worker process)
            result = self.tools[task.tool](task.inputs)
            logger.debug(f"Task {task.task_id} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Task {task.task_id} failed with error: {e}")
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                # Exponential backoff
                time.sleep(1 * (2 ** task.retry_count)) 
                logger.info(f"Retrying task {task.task_id} (Attempt {task.retry_count}/{task.max_retries})")
                return self.execute_task(task)
            return {"error": str(e), "status": "failed"}

    def execute_plan(self, plan: TaskDAG) -> Dict[str, Any]:
        """Execute all tasks in a plan DAG, respecting dependencies."""
        results = {}
        sorted_tasks = plan.topological_sort()
        
        # Parallel execution can be achieved here with asyncio
        # Doing sequentially for MVP
        for task in sorted_tasks:
            # Check dependencies
            deps_met = all(dep in results and "error" not in results[dep] for dep in task.dependencies)
            
            if not deps_met and len(task.dependencies) > 0:
                logger.error(f"Dependencies not met for task {task.task_id}. Skipping.")
                results[task.task_id] = {"error": "Dependencies failed"}
                continue
                
            task_result = self.execute_task(task)
            results[task.task_id] = task_result
            
        return results
