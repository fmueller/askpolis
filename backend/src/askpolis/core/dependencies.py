from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from askpolis.db import get_db

from .models import Tenant
from .repositories import DocumentRepository, ParliamentRepository
from .tenant_repository import TenantRepository


def get_document_repository(db: Annotated[Session, Depends(get_db)]) -> DocumentRepository:
    return DocumentRepository(db)


def get_parliament_repository(db: Annotated[Session, Depends(get_db)]) -> ParliamentRepository:
    return ParliamentRepository(db)


def get_tenant_repository(
    parliament_repository: Annotated[ParliamentRepository, Depends(get_parliament_repository)],
) -> TenantRepository:
    return TenantRepository(parliament_repository)


def get_tenant(
    request: Request,
    tenant_repository: Annotated[TenantRepository, Depends(get_tenant_repository)],
    x_tenant: Annotated[str | None, Header(alias="X-Tenant", convert_underscores=False)] = None,
) -> Tenant:
    tenant_name = x_tenant or request.headers.get("X-Tenant") or "demo"
    tenant = tenant_repository.get(tenant_name)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_name}' not found",
        )
    return tenant
