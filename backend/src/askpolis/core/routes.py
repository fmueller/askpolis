from typing import Annotated

import uuid_utils.compat as uuid
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .dependencies import (
    get_document_repository,
    get_page_repository,
    get_parliament_repository,
)
from .models import (
    CreateParliamentRequest,
    DocumentResponse,
    PageResponse,
    Parliament,
    ParliamentResponse,
)
from .repositories import DocumentRepository, PageRepository, ParliamentRepository

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


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    tags=["documents"],
)
def get_document(
    document_id: Annotated[uuid.UUID, Path()],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> DocumentResponse:
    document = document_repository.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(id=document.id, name=document.name, document_type=document.document_type)


@router.get(
    "/documents/{document_id}/pages/{page_id}",
    response_model=PageResponse,
    tags=["documents"],
)
def get_document_page(
    document_id: Annotated[uuid.UUID, Path()],
    page_id: Annotated[uuid.UUID, Path()],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    page_repository: Annotated[PageRepository, Depends(get_page_repository)],
) -> PageResponse:
    document = document_repository.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    page = page_repository.get(page_id)
    if page is None or page.document_id != document_id:
        raise HTTPException(status_code=404, detail="Page not found")
    return PageResponse(
        id=page.id,
        document_id=page.document_id,
        page_number=page.page_number,
        content=page.content,
        page_metadata=page.page_metadata,
    )
