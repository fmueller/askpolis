from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .dependencies import get_parliament_repository
from .models import CreateParliamentRequest, Parliament, ParliamentResponse
from .repositories import ParliamentRepository

router = APIRouter()


@router.post(
    "/parliaments", status_code=status.HTTP_201_CREATED, response_model=ParliamentResponse, tags=["parliaments"]
)
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
