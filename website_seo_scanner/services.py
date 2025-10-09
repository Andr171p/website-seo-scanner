from .ai.utils import generate_search_queries
from .report import PageReport, form_page_report
from .schemas import AboutSite
from .tree import build_site_tree, extract_key_pages
from .utils import SearchResult, websearch

DEFAULT_MAX_PAGE_RESULTS = 7


async def search_site_competitors(
        about_site: AboutSite, max_page_results: int = DEFAULT_MAX_PAGE_RESULTS
) -> list[SearchResult]:
    """Выполняет поиск потенциальных конкурентов сайта, основываясь на информации о нём.

    :param about_site: Информация о текущем сайте.
    :param max_page_results: Максимальное количество сайтов конкурентов на странице.
    :return Список уникальных результатов поиска.
    """
    results: set[SearchResult] = set()
    queries = await generate_search_queries(about_site)
    for query in queries:
        results.update(websearch(query, max_results=max_page_results))
    return list(results)


async def analyze_site_seo_optimization(url: str) -> ...:
    site_tree = build_site_tree(url)
    pages = extract_key_pages(site_tree)
    page_reports: list[PageReport] = []
    for page in pages:
        page_report = await form_page_report(page)
        page_reports.append(page_report)
    return page_reports
