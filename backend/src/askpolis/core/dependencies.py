from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from askpolis.db import get_db

from .repositories import DocumentRepository, ParliamentRepository


def get_document_repository(db: Annotated[Session, Depends(get_db)]) -> DocumentRepository:
    return DocumentRepository(db)


def get_parliament_repository(db: Annotated[Session, Depends(get_db)]) -> ParliamentRepository:
    return ParliamentRepository(db)
