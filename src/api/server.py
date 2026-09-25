from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn
import logging

from ..agent.orchestrator import AgentOrchestrator
from .auth import verify_token

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent-as-Database API",
    description="Production API for Semantic Knowledge Graph Query Engine",
    version="2.0.0"
)

security = HTTPBearer()

# Note: Orchestrator instantiation should ideally be cached/singleton in a real app
orchestrator = AgentOrchestrator()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query_id: str
    query: str
    claims: list
    execution_summary: dict
    freshness_score: float

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Process a natural language query with authentication.
    Requires Bearer token (e.g. 'admin-secret-token-123').
    """
    try:
        # 1. Verify token
        user = verify_token(credentials.credentials)
        tenant_id = f"tenant_{user}"
        logger.info(f"User '{user}' (Tenant: {tenant_id}) requested query: {request.query}")
        
        # 2. Execute agent orchestrator
        result = orchestrator.process_query(request.query, tenant_id=tenant_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing API query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Kubernetes health check endpoint."""
    return {"status": "healthy", "version": "2.0.0", "cache": "connected"}

def start_server(host="0.0.0.0", port=8000):
    """Entry point for starting the uvicorn server."""
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run("src.api.server:app", host=host, port=port, reload=False)
