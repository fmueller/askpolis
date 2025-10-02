from typing import Annotated

import uuid_utils.compat as uuid
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import JSONResponse

from askpolis.jsonapi import JsonApiRequest, JsonApiResponse, jsonapi_response

from .dependencies import (
    get_document_repository,
    get_parliament_repository,
)
from .models import (
    DocumentAttributes,
    PageAttributes,
    Parliament,
    ParliamentAttributes,
)
from .repositories import DocumentRepository, ParliamentRepository

router = APIRouter()


@router.post(
    "/parliaments",
    status_code=status.HTTP_201_CREATED,
    response_model=JsonApiResponse[ParliamentAttributes],
    tags=["parliaments"],
)
def create_parliament(
    payload: JsonApiRequest[ParliamentAttributes],
    parliament_repository: Annotated[ParliamentRepository, Depends(get_parliament_repository)],
) -> JSONResponse:
    attrs = payload.data.attributes
    parliament = parliament_repository.get_by_name(attrs.name)
    if parliament is not None:
        raise HTTPException(status_code=409, detail="Parliament already exists")
    parliament = Parliament(attrs.name, attrs.short_name)
    parliament_repository.save(parliament)
    return jsonapi_response(
        "parliaments",
        parliament.id,
        ParliamentAttributes(name=attrs.name, short_name=attrs.short_name),
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "/documents/{document_id}",
    response_model=JsonApiResponse[DocumentAttributes],
    tags=["documents"],
)
def get_document(
    document_id: Annotated[uuid.UUID, Path()],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> JSONResponse:
    document = document_repository.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return jsonapi_response(
        "documents",
        document.id,
        DocumentAttributes(name=document.name, document_type=document.document_type),
    )


@router.get(
    "/documents/{document_id}/pages/{page_id}",
    response_model=JsonApiResponse[PageAttributes],
    tags=["documents"],
)
def get_document_page(
    document_id: Annotated[uuid.UUID, Path()],
    page_id: Annotated[uuid.UUID, Path()],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> JSONResponse:
    document = document_repository.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    page = document_repository.get_page(document_id, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return jsonapi_response(
        "pages",
        page.id,
        PageAttributes(
            document_id=page.document_id,
            page_number=page.page_number,
            content=page.content,
            page_metadata=page.page_metadata,
        ),
    )
