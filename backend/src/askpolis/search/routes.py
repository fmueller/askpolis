from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from askpolis.celery import app as celery_app

from .dependencies import get_search_service
from .models import SearchResponse
from .search_service import SearchService

router = APIRouter()


@router.get("/tasks/embeddings", tags=["tasks", "embeddings", "search"])
def trigger_embeddings_ingestion() -> JSONResponse:
    celery_app.send_task("ingest_embeddings_for_one_document")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@router.get("/tasks/tests/embeddings", tags=["tasks", "embeddings", "search"])
def trigger_embeddings_test() -> JSONResponse:
    celery_app.send_task("test_embeddings")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@router.get("/search", tags=["search"])
def search(
    search_service: Annotated[SearchService, Depends(get_search_service)],
    query: str,
    limit: int = 5,
    reranking: bool = False,
    index: Annotated[list[str] | None, Query()] = None,
) -> SearchResponse:
    if index is None:
        index = ["default"]
    if limit < 1:
        limit = 5
    return SearchResponse(query=query, results=search_service.find_matching_texts(query, limit, reranking, index))
