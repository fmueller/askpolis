from typing import Any

import uuid_utils.compat as uuid
from pydantic import BaseModel


class SearchResult(BaseModel):
    matching_text: str
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    metadata: dict[str, Any]
    score: float
