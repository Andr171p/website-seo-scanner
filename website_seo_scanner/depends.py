from typing import Final

import spacy
from langchain_core.language_models import BaseChatModel

nlp: Final[spacy.Language] = ...

llm: Final[BaseChatModel] = ...
