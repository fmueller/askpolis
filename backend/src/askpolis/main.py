from fastapi import FastAPI
from pydantic import BaseModel

from askpolis.core import router as core_router
from askpolis.logging import get_logger
from askpolis.qa import router as qa_router
from askpolis.rate_limiting import RateLimitMiddleware
from askpolis.search import router as search_router

logger = get_logger(__name__)
logger.info("Starting AskPolis API...")

api_version = "v0"
api_base_path = f"/{api_version}"

app = FastAPI()
app.add_middleware(RateLimitMiddleware)
app.include_router(core_router, prefix=api_base_path)
app.include_router(qa_router, prefix=api_base_path)
app.include_router(search_router, prefix=api_base_path)


class HealthResponse(BaseModel):
    healthy: bool


@app.get("/")
def read_root() -> HealthResponse:
    return HealthResponse(healthy=True)
