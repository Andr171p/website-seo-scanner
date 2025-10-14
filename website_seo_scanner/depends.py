from typing import Final

import spacy
from embeddings_service.langchain import RemoteHTTPEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

nlp: Final[spacy.Language] = ...

llm: Final[BaseChatModel] = ...

embeddings: Final[Embeddings] = RemoteHTTPEmbeddings(
    base_url="http://10.1.50.57:8005", timeout=120
)
