from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from askpolis.core import router as core_router
from askpolis.jsonapi import JsonApiResponse, jsonapi_response
from askpolis.logging import get_logger
from askpolis.qa import router as qa_router
from askpolis.rate_limiting import RateLimitMiddleware
from askpolis.search import router as search_router

logger = get_logger(__name__)
logger.info("Starting AskPolis API...")

api_version = "v0"
api_base_path = f"/{api_version}"

app = FastAPI(docs_url="/")
app.add_middleware(RateLimitMiddleware)
app.include_router(core_router, prefix=api_base_path)
app.include_router(qa_router, prefix=api_base_path)
app.include_router(search_router, prefix=api_base_path)


class HealthAttributes(BaseModel):
    healthy: bool


@app.get("/healthz", include_in_schema=False, response_model=JsonApiResponse[HealthAttributes])
def liveness_probe() -> JSONResponse:
    """Endpoint used by Kubernetes liveness probe."""
    return jsonapi_response("health", "healthz", HealthAttributes(healthy=True))


@app.get("/readyz", include_in_schema=False, response_model=JsonApiResponse[HealthAttributes])
def readiness_probe() -> JSONResponse:
    """Endpoint used by Kubernetes readiness probe."""
    return jsonapi_response("health", "readyz", HealthAttributes(healthy=True))
