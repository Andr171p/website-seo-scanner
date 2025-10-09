from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from pydantic import BaseModel, Field, HttpUrl

from ..depends import llm
from .prompts import SEARCH_QUERIES_GENERATION_PROMPT

DEFAULT_MAX_RESULTS = 15


class SearchQueriesResponse(BaseModel):
    search_queries: list[str] = Field(
        default_factory=list, description="Поисковые запросы"
    )


class AboutSite(BaseModel):
    """Информация о сайте

    Attributes:
        url: Адрес сайта.
        title: Название компании/сайта.
        description: Описание компании/сайта.
        industry: Отрасль или ниша.
        target_audience: Целевая аудитория.
        target_location: Целевой регион или город.
        main_products: Основные продукты, услуги и.т.д компании.
        key_features: Ключевые преимущества.
    """
    url: HttpUrl
    title: str
    description: str
    industry: str
    target_audience: str
    target_location: str
    main_products: list[str]
    key_features: list[str]


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
