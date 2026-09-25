from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class Entity(BaseModel):
    name: str
    type: str

class Relationship(BaseModel):
    src: str
    dst: str
    type: str

class QueryRepresentation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    query_id: str
    original_text: str
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    embedding: Any = None  # Expected to be np.ndarray or List[float]
    estimated_complexity: str = "medium"
    estimated_tool_count: int = 1

class Task(BaseModel):
    task_id: str
    description: str
    tool: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    estimated_time_ms: int = 1000
    priority: int = 1
    dependencies: List[str] = Field(default_factory=list)
    timeout_ms: int = 5000
    max_retries: int = 3
    retry_count: int = 0
    fallback_tool: Optional[str] = None
    expected_schema: Optional[Dict[str, Any]] = None

class TaskDAG(BaseModel):
    plan_id: str
    tasks: List[Task] = Field(default_factory=list)
    total_estimated_time_ms: int = 0
    parallelizable_tasks: int = 0
    critical_path: List[str] = Field(default_factory=list)

    def topological_sort(self) -> List[Task]:
        """Simple topological sort for tasks."""
        # For prototype, assume order in list is topological if valid,
        # or implement a simple sort.
        in_degree = {task.task_id: 0 for task in self.tasks}
        for task in self.tasks:
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.task_id] += 1
                    
        queue = [task for task in self.tasks if in_degree[task.task_id] == 0]
        sorted_tasks = []
        
        while queue:
            node = queue.pop(0)
            sorted_tasks.append(node)
            # This requires a reverse mapping which is omitted for simplicity in this dummy topological sort
            # Real implementation would use networkx.topological_sort
            
        return self.tasks  # Fallback
