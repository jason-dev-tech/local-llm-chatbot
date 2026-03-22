from openai import OpenAI

from config import API_KEY, BASE_URL, EMBEDDING_MODEL


class EmbeddingService:
    def __init__(
        self,
        base_url: str = BASE_URL,
        api_key: str = API_KEY,
        model_name: str = EMBEDDING_MODEL,
    ) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text,
        )
        return response.data[0].embedding