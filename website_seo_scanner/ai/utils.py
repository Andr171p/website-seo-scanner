from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel, Field, HttpUrl

from ..depends import llm
from ..schemas import AboutSite
from .prompts import SEARCH_QUERIES_GENERATION_PROMPT

DEFAULT_MAX_RESULTS = 15


class SearchQueriesResponse(BaseModel):
    search_queries: list[str] = Field(
        default_factory=list, description="Поисковые запросы"
    )


class KeySectionsResponse(BaseModel):
    key_sections: list[str] = Field(
        default_factory=list, description="Ключевые разделы сайта для seo анализа"
    )


async def generate_search_queries(
        about_site: AboutSite, max_results: int = DEFAULT_MAX_RESULTS
) -> list[str]:
    """Генерирует гипотетические и косвенные поисковые запросы

    :param about_site: Подробна информация о сайте.
    :param max_results: Максимальное количество сгенерированных поисковых запросов.
    :return Список потенциальных поисковых запросов.
    """
    parser = PydanticOutputParser(pydantic_object=SearchQueriesResponse)
    prompt = (
        ChatPromptTemplate
        .from_messages([("system", SEARCH_QUERIES_GENERATION_PROMPT)])
        .partial(format_instructions=parser.get_format_instructions())
    )
    chain: RunnableSerializable[dict[str, str | int], SearchQueriesResponse] = (
        prompt
        | llm
        | parser
    )
    response = await chain.ainvoke({**about_site.model_dump(), "max_result": max_results})
    return response.search_queries[::max_results]


async def generate_key_sections(
        url: HttpUrl, title: str, max_results: int = DEFAULT_MAX_RESULTS
) -> list[str]:
    """Генерирует ключевые разделы сайта,
    которые могут быть полезны для SEO анализа.

    :param url: URL адрес сайта.
    :param title: Заголовок, название сайта.
    :param max_results: Максимальное количество генерируемых разделов.
    :return список ключевых разделов сайта.
    """
    parser = PydanticOutputParser(pydantic_object=KeySectionsResponse)
    prompt = (
        ChatPromptTemplate
        .from_messages([("system", ...)])
        .partial(format_instructions=parser.get_format_instructions())
    )
    chain: RunnableSerializable[dict[str, str], KeySectionsResponse] = prompt | llm | parser
    response = await chain.ainvoke({"url": url, "title": title, "max_results": max_results})
    return response.key_sections[::max_results]
