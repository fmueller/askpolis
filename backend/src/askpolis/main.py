from typing import Annotated

import uuid_utils.compat as uuid
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from askpolis.core import Parliament, ParliamentRepository, get_parliament_repository
from askpolis.logging import get_logger
from askpolis.qa import router as qa_router
from askpolis.search import router as search_router

logger = get_logger(__name__)
logger.info("Starting AskPolis API...")

app = FastAPI()
app.include_router(qa_router, prefix="/v0")
app.include_router(search_router, prefix="/v0")


class HealthResponse(BaseModel):
    healthy: bool


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
