from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from askpolis.celery import app as celery_app
from askpolis.jsonapi import JsonApiResponse, jsonapi_response

from .dependencies import get_search_service
from .models import SearchResponse, StatusAttributes
from .search_service import SearchService

router = APIRouter()


@router.get(
    "/tasks/embeddings",
    tags=["tasks", "embeddings", "search"],
    response_model=JsonApiResponse[StatusAttributes],
)
def trigger_embeddings_ingestion() -> JSONResponse:
    celery_app.send_task("ingest_embeddings_for_one_document")
    return jsonapi_response(
        "tasks",
        None,
        StatusAttributes(status="ok"),
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.get(
    "/tasks/tests/embeddings",
    tags=["tasks", "embeddings", "search"],
    response_model=JsonApiResponse[StatusAttributes],
)
def trigger_embeddings_test() -> JSONResponse:
    celery_app.send_task("test_embeddings")
    return jsonapi_response(
        "tasks",
        None,
        StatusAttributes(status="ok"),
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.get("/search", tags=["search"], response_model=JsonApiResponse[SearchResponse])
def search(
    request: Request,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    query: str,
    limit: int = 5,
    reranking: bool = False,
    index: Annotated[list[str] | None, Query()] = None,
) -> JSONResponse:
    if index is None:
        index = ["default"]
    if limit < 1:
        limit = 5
    results = search_service.find_matching_texts(query, limit, reranking, index)
    for r in results:
        r.document_url = str(request.url_for("get_document", document_id=r.document_id))
        r.page_url = str(
            request.url_for(
                "get_document_page",
                document_id=r.document_id,
                page_id=r.page_id,
            )
        )
    return jsonapi_response(
        "search-results",
        None,
        SearchResponse(query=query, results=results),
    )
