from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingsService:
    def __init__(self, model_name: str):
        self._embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"trust_remote_code": True},
            encode_kwargs={"normalize_embeddings": True},
        )
