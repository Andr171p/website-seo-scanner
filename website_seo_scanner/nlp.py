from typing import Final, Literal

import spacy
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nlp: Final[spacy.Language] = ...

llm: Final[BaseChatModel] = ...


class KeywordsResponse(BaseModel):
    """Ответ LLM с извлечёнными ключевыми словами"""
    keywords: list[str] = Field(..., description="Ключевые слова на странице")


def compare_texts(text1: str, text2: str) -> float:
    """Сравнивает релевантность двух текстов"""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


def extract_keywords(text: str, strategy: Literal["llm", "ml"]) -> list[str]:
    """Извлекает ключевые слова из текста.

    :param text: Текст для извлечения ключевых слов.
    :param strategy: Стратегия для извлечения: 'llm', 'ml'
    """
    match strategy:
        case "ml":
            document = nlp(text)
            return [
                token.text for token in document if token.pos_ in {"NOUN", "PROPN", "ADJ"}
            ]
        case "llm":
            parser = PydanticOutputParser(pydantic_object=KeywordsResponse)
            prompt = (
                ChatPromptTemplate
                .from_messages(["system", ...])
                .partial(format_instructions=parser.get_format_instructions())
            )
            chain: RunnableSerializable[dict[str, str], KeywordsResponse] = prompt | llm | parser
            response = chain.invoke({"text": text})
            return response.keywords
