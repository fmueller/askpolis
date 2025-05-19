import os
from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from askpolis.logging import get_logger
from askpolis.qa.models import Answer, AnswerContent, Citation, Question
from askpolis.search import SearchServiceBase

logger = get_logger(__name__)

_agent = Agent(
    OpenAIModel(
        model_name="llama3.1",
        provider=OpenAIProvider(base_url=os.getenv("OLLAMA_URL") or "http://localhost:11434/v1", api_key="ollama"),
    ),
    model_settings=ModelSettings(
        max_tokens=512,
        temperature=0.7,
        top_p=0.9,
    ),
    system_prompt="""
    Answer the query by using ONLY the provided content below.
    Respond with NO_ANSWER if the content is not relevant for answering the query.
    Do NOT add additional information.
    Be concise and respond succinctly using Markdown.
    """,
)


class AnswerAgent:
    def __init__(self, search_service: SearchServiceBase) -> None:
        self._search_service = search_service

    def answer(self, question: Question) -> Optional[Answer]:
        logger.info_with_attrs("Querying...", {"question": question.content})
        results = self._search_service.find_matching_texts(question.content, limit=5, use_reranker=True)

        logger.info("Invoking LLM chain...")
        content = "\n\n".join([r.matching_text for r in results])
        answer = _agent.run_sync(user_prompt=f"Query: {question}\n\nContent:\n\n{content}")
        if answer is not None and answer.output.strip() != "NO_ANSWER":
            return Answer(
                contents=[AnswerContent(language="de", content=answer.output.strip())],
                citations=[Citation(r) for r in results],
            )

        logger.warning_with_attrs(
            "No answer was generated", attrs={"question": question.content, "answer": answer.output}
        )
        return None
