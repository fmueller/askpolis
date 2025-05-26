from typing import Annotated

import uuid_utils.compat as uuid
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from askpolis.celery import app as celery_app
from askpolis.core import Parliament, ParliamentRepository, get_parliament_repository
from askpolis.logging import configure_logging, get_logger
from askpolis.qa import router as qa_router
from askpolis.search import SearchResult, SearchService, get_search_service

configure_logging()

logger = get_logger(__name__)
logger.info("Starting AskPolis API...")

app = FastAPI()
app.include_router(qa_router, prefix="/v0")


class HealthResponse(BaseModel):
    healthy: bool


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class ParliamentResponse(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str


class CreateParliamentRequest(BaseModel):
    name: str = Field()
    short_name: str = Field()


@app.get("/")
def read_root() -> HealthResponse:
    return HealthResponse(healthy=True)


@app.get("/v0/tasks/embeddings")
def trigger_embeddings_ingestion() -> JSONResponse:
    celery_app.send_task("ingest_embeddings_for_one_document")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@app.get("/v0/tasks/tests/embeddings")
def trigger_embeddings_test() -> JSONResponse:
    celery_app.send_task("test_embeddings")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@app.post("/v0/parliaments", status_code=status.HTTP_201_CREATED, response_model=ParliamentResponse)
def create_parliament(
    payload: CreateParliamentRequest,
    parliament_repository: Annotated[ParliamentRepository, Depends(get_parliament_repository)],
) -> JSONResponse:
    parliament = parliament_repository.get_by_name(payload.name)
    if parliament is not None:
        raise HTTPException(status_code=409, detail="Parliament already exists")
    parliament = Parliament(payload.name, payload.short_name)
    parliament_repository.save(parliament)
    return JSONResponse(
        content=jsonable_encoder(
            ParliamentResponse(
                id=parliament.id,
                name=payload.name,
                short_name=payload.short_name,
            )
        ),
        status_code=status.HTTP_201_CREATED,
    )


@app.get("/v0/search")
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
