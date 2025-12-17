from typing import Annotated

import uuid_utils.compat as uuid
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from askpolis.core import Document, DocumentRepository, Tenant, get_document_repository, get_tenant
from askpolis.search import Embeddings, EmbeddingsRepository, get_embeddings_repository

from .dependencies import get_qa_service, get_question_repository
from .models import AnswerResponse, CitationResponse, CreateQuestionRequest, Question, QuestionResponse
from .qa_service import QAService
from .repositories import QuestionRepository

router = APIRouter(prefix="/questions", responses={404: {"description": "Question not found"}}, tags=["questions"])


def get_question_from_path(
    question_id: Annotated[uuid.UUID, Path()],
    tenant: Annotated[Tenant, Depends(get_tenant)],
    question_repository: Annotated[QuestionRepository, Depends(get_question_repository)],
) -> Question:
    question = question_repository.get_for_tenant(tenant.id, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post(path="/", status_code=status.HTTP_201_CREATED, response_model=QuestionResponse)
def create_question(
    request: Request,
    payload: CreateQuestionRequest,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    qa_service: Annotated[QAService, Depends(get_qa_service)],
) -> JSONResponse:
    question = qa_service.add_question(tenant, payload.question)
    return JSONResponse(
        # TODO can we remove this encoder call?
        content=jsonable_encoder(
            QuestionResponse(
                id=question.id,
                content=payload.question,
                status="pending",
                answer_url=str(request.url_for("get_answer", question_id=question.id)),
                created_at=question.created_at.isoformat(),
                updated_at=question.updated_at.isoformat(),
            )
        ),
        status_code=status.HTTP_201_CREATED,
        headers={"Location": str(request.url_for("get_question", question_id=question.id))},
    )


@router.get(path="/{question_id}", response_model=QuestionResponse)
def get_question(
    request: Request,
    question: Annotated[Question, Depends(get_question_from_path)],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    embeddings_repository: Annotated[EmbeddingsRepository, Depends(get_embeddings_repository)],
) -> QuestionResponse:
    if len(question.answers) == 0:
        answer_response = AnswerResponse(status="in_progress", citations=[])
    else:
        answer = question.answers[0]
        if len(answer.contents) == 0:
            raise HTTPException(status_code=500, detail="Answer without content pieces should not exist")

        document_ids = [cit.document_id for cit in answer.citations]
        embedding_ids = [cit.embeddings_id for cit in answer.citations]

        documents = {
            doc.id: doc for doc in document_repository.db.query(Document).filter(Document.id.in_(document_ids)).all()
        }
        embeddings = {
            emb.id: emb
            for emb in embeddings_repository.db.query(Embeddings).filter(Embeddings.id.in_(embedding_ids)).all()
        }

        citation_responses: list[CitationResponse] = []
        for cit in answer.citations:
            doc = documents.get(cit.document_id)
            emb = embeddings.get(cit.embeddings_id)

            title = doc.name if doc and doc.name else "Unknown"
            content = emb.chunk if emb and emb.chunk else "Unknown"
            url = str(
                request.url_for(
                    "get_document_page",
                    document_id=cit.document_id,
                    page_id=cit.page_id,
                )
            )

            citation_responses.append(
                CitationResponse(
                    title=title,
                    content=content,
                    url=url,
                )
            )

        answer_response = AnswerResponse(
            answer=answer.contents[0].content,
            language=answer.contents[0].language.strip(),
            status="completed",
            citations=citation_responses,
            created_at=answer.created_at.isoformat(),
            updated_at=answer.updated_at.isoformat(),
        )

    return QuestionResponse(
        id=question.id,
        content=question.content,
        status="pending" if len(question.answers) == 0 else "answered",
        answer_url=str(request.url_for("get_answer", question_id=question.id)),
        created_at=question.created_at.isoformat(),
        updated_at=question.updated_at.isoformat(),
        answer=answer_response,
    )


@router.get(
    path="/{question_id}/answer",
    response_model=AnswerResponse,
    responses={
        500: {"description": "Answer without content pieces should not exist"},
    },
)
def get_answer(
    request: Request,
    question: Annotated[Question, Depends(get_question_from_path)],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    embeddings_repository: Annotated[EmbeddingsRepository, Depends(get_embeddings_repository)],
) -> AnswerResponse:
    if len(question.answers) == 0:
        return AnswerResponse(
            status="in_progress",
            citations=[],
        )

    answer = question.answers[0]
    if len(answer.contents) == 0:
        raise HTTPException(status_code=500, detail="Answer without content pieces should not exist")

    document_ids = [cit.document_id for cit in answer.citations]
    embedding_ids = [cit.embeddings_id for cit in answer.citations]

    documents = {
        doc.id: doc for doc in document_repository.db.query(Document).filter(Document.id.in_(document_ids)).all()
    }
    embeddings = {
        emb.id: emb for emb in embeddings_repository.db.query(Embeddings).filter(Embeddings.id.in_(embedding_ids)).all()
    }

    citation_responses: list[CitationResponse] = []
    for cit in answer.citations:
        doc = documents.get(cit.document_id)
        emb = embeddings.get(cit.embeddings_id)
        title = doc.name if doc and doc.name else "Unknown"
        content = emb.chunk if emb and emb.chunk else "Unknown"
        url = str(
            request.url_for(
                "get_document_page",
                document_id=cit.document_id,
                page_id=cit.page_id,
            )
        )
        citation_responses.append(
            CitationResponse(
                title=title,
                content=content,
                url=url,
            )
        )

    return AnswerResponse(
        answer=answer.contents[0].content,
        language=answer.contents[0].language.strip(),
        status="completed",
        citations=citation_responses,
        created_at=answer.created_at.isoformat(),
        updated_at=answer.updated_at.isoformat(),
    )
