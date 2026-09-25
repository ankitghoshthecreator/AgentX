import time
import logging
import requests
import re
import urllib.parse
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Executes tasks with a dynamic tool registry, retries, and fallback support."""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.register_tool("web_search", self._wikipedia_search)
        self.register_tool("duckduckgo_search", self._duckduckgo_search)
        self.register_tool("github_api", self._mock_github_api)
        self.register_tool("semantic_extract", self._mock_semantic_extract)
        logger.info("TaskExecutor initialized with extensible tool registry.")

    def register_tool(self, tool_name: str, executable: Callable):
        """Register any callable as a named tool (supports MCP integration in Phase 3)."""
        self.tools[tool_name] = executable
        logger.debug(f"Tool registered: {tool_name}")

    # ── Real Tool: Wikipedia Search ────────────────────────────────────────────
    def _wikipedia_search(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs.get('query', '')
        try:
            logger.info(f"Wikipedia search: {query}")
            safe_query = urllib.parse.quote(query)
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&utf8=&format=json"
            headers = {'User-Agent': 'AgentAsDatabase/2.0 (research-agent)'}
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code != 200:
                return {"error": f"Wikipedia HTTP {response.status_code}", "source": "wikipedia"}
            data = response.json()
            hits = data.get('query', {}).get('search', [])
            if hits:
                snippet = re.sub('<[^<]+>', '', hits[0]['snippet'])
                return {"results": [snippet], "source": "wikipedia", "title": hits[0].get('title', '')}
            return {"results": ["No results found."], "source": "wikipedia"}
        except Exception as e:
            return {"error": str(e), "source": "wikipedia"}

    # ── Real Tool: DuckDuckGo Instant Answer ──────────────────────────────────
    def _duckduckgo_search(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = inputs.get('query', '')
        try:
            logger.info(f"DuckDuckGo search: {query}")
            safe_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={safe_query}&format=json&no_html=1&skip_disambig=1"
            headers = {'User-Agent': 'AgentAsDatabase/2.0'}
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code != 200:
                return {"error": f"DuckDuckGo HTTP {response.status_code}", "source": "duckduckgo"}
            data = response.json()
            abstract = data.get('AbstractText', '')
            answer = data.get('Answer', '')
            result = abstract or answer or "No instant answer available."
            return {"results": [result], "source": "duckduckgo", "type": data.get('Type', '')}
        except Exception as e:
            return {"error": str(e), "source": "duckduckgo"}

    # ── Mock Tool: GitHub API ─────────────────────────────────────────────────
    def _mock_github_api(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.15)
        return {
            "stars": 12400,
            "forks": 1800,
            "open_issues": 234,
            "description": f"Repository data for {inputs.get('query')}",
            "source": "github_mock"
        }

    # ── Mock Tool: Semantic Extract ───────────────────────────────────────────
    def _mock_semantic_extract(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.15)
        entities = inputs.get('entities', [])
        return {
            "extracted": f"Comparative semantic properties extracted for: {', '.join(entities)}",
            "source": "semantic_extract"
        }

    # ── Execution ─────────────────────────────────────────────────────────────
    def execute_task(self, task) -> Dict[str, Any]:
        logger.info(f"Executing [{task.task_id}] '{task.description}' using tool='{task.tool}'")
        
        active_tool = task.tool
        if active_tool not in self.tools:
            if task.fallback_tool and task.fallback_tool in self.tools:
                logger.warning(f"Tool '{active_tool}' not found. Using fallback '{task.fallback_tool}'.")
                active_tool = task.fallback_tool
            else:
                return {"error": f"Tool '{active_tool}' not registered and no fallback available."}

        try:
            result = self.tools[active_tool](task.inputs)
            if "error" in result:
                logger.warning(f"Task [{task.task_id}] tool returned error: {result['error']}")
            return result
        except Exception as e:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                backoff = 0.5 * (2 ** task.retry_count)
                logger.warning(f"Retrying [{task.task_id}] in {backoff:.1f}s (attempt {task.retry_count}/{task.max_retries})")
                time.sleep(backoff)
                return self.execute_task(task)
            logger.error(f"Task [{task.task_id}] permanently failed: {e}")
            return {"error": str(e), "status": "permanently_failed"}

    def execute_plan(self, plan) -> Dict[str, Any]:
        results = {}
        for task in plan.topological_sort():
            deps_ok = all(dep in results and "error" not in results[dep] for dep in task.dependencies)
            if task.dependencies and not deps_ok:
                logger.error(f"Skipping [{task.task_id}]: dependencies not met.")
                results[task.task_id] = {"error": "Dependency failed upstream"}
                continue
            results[task.task_id] = self.execute_task(task)
        return results
