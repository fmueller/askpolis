from typing import Annotated

import uuid_utils.compat as uuid
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from askpolis.core import DocumentRepository, get_document_repository
from askpolis.qa import get_qa_service
from askpolis.qa.models import AnswerResponse, CitationResponse, CreateQuestionRequest, Question, QuestionResponse
from askpolis.qa.qa_service import QAService
from askpolis.search import EmbeddingsRepository, get_embeddings_repository

router = APIRouter(prefix="/questions", tags=["questions"])


def get_question_from_path(
    question_id: Annotated[uuid.UUID, Path()],
    qa_service: Annotated[QAService, Depends(get_qa_service)],
) -> Question:
    question = qa_service.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post(path="/", status_code=status.HTTP_201_CREATED, response_model=QuestionResponse)
def create_question(
    request: Request, payload: CreateQuestionRequest, qa_service: Annotated[QAService, Depends(get_qa_service)]
) -> JSONResponse:
    question = qa_service.add_question(payload.question)
    return JSONResponse(
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


@router.get(
    path="/{question_id}",
    response_model=QuestionResponse,
    responses={404: {"description": "Question not found"}},
)
def get_question(
    request: Request,
    question: Annotated[Question, Depends(get_question_from_path)],
) -> QuestionResponse:
    return QuestionResponse(
        id=question.id,
        content=question.content,
        status="pending" if len(question.answers) == 0 else "answered",
        answer_url=str(request.url_for("get_answer", question_id=question.id)),
        created_at=question.created_at.isoformat(),
        updated_at=question.updated_at.isoformat(),
    )


@router.get(
    path="/{question_id}/answer",
    response_model=AnswerResponse,
    responses={
        404: {"description": "Question not found"},
        500: {"description": "Answer without content pieces should not exist"},
    },
)
def get_answer(
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

    citation_responses: list[CitationResponse] = []
    for cit in answer.citations:
        doc = document_repository.get(cit.document_id)
        emb = embeddings_repository.get(cit.embeddings_id)

        title = doc.name if doc and doc.name else "Unknown"
        content = emb.chunk if emb and emb.chunk else "Unknown"

        citation_responses.append(
            CitationResponse(
                title=title,
                content=content,
            )
        )

    return AnswerResponse(
        answer=answer.contents[0].content,
        language=answer.contents[0].language,
        status="completed",
        citations=citation_responses,
        created_at=answer.created_at.isoformat(),
        updated_at=answer.updated_at.isoformat(),
    )
