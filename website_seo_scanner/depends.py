from typing import Final

from embeddings_service.langchain import RemoteHTTPEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from .settings import settings

embeddings: Final[Embeddings] = RemoteHTTPEmbeddings(
    base_url=settings.embeddings.base_url, timeout=240
)

llm: Final[BaseChatModel] = ...
