from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonApiResource(BaseModel, Generic[T]):
    type: str
    id: str | None = None
    attributes: T


class JsonApiResponse(BaseModel, Generic[T]):
    data: JsonApiResource[T]


class JsonApiRequest(BaseModel, Generic[T]):
    data: JsonApiResource[T]


def jsonapi_response(
    resource_type: str,
    resource_id: str | UUID | None,
    attributes: T,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    resource = JsonApiResource(
        type=resource_type,
        id=str(resource_id) if resource_id is not None else None,
        attributes=attributes,
    )
    payload = JsonApiResponse(data=resource)
    return JSONResponse(content=payload.model_dump(mode="json"), status_code=status_code, headers=headers)
