import os

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

from askpolis.logging import get_logger
from askpolis.search import SearchServiceBase

from .models import Answer, AnswerContent, Citation, Question

logger = get_logger(__name__)

_agent = Agent(
    OpenAIChatModel(
        model_name=os.getenv("OLLAMA_MODEL") or "mistral:7b",
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

    def answer(self, question: Question) -> Answer | None:
        logger.info_with_attrs("Querying...", {"question": question.content})
        results = self._search_service.find_matching_texts(question.content, limit=5, use_reranker=True)

        logger.info("Invoking LLM chain...")
        content = "\n\n".join([r.matching_text for r in results])
        answer = _agent.run_sync(user_prompt=f"Query: {question}\n\nContent:\n\n{content}")
        if answer is None:
            logger.warning_with_attrs("No answer was generated", attrs={"question": question.content})
            return None

        # for now, we also store NO_ANSWER in the database
        return Answer(
            contents=[AnswerContent(language="de", content=answer.output.strip())],
            citations=[Citation(r) for r in results],
        )
