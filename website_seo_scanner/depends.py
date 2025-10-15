from typing import Final

from embeddings_service.langchain import RemoteHTTPEmbeddings
from langchain_core.embeddings import Embeddings

from .settings import settings

embeddings: Final[Embeddings] = RemoteHTTPEmbeddings(
    base_url=settings.embeddings.base_url, timeout=120
)
