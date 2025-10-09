import logging

from bs4 import BeautifulSoup
from ddgs import DDGS
from playwright.async_api import Browser, Page
from pydantic import BaseModel, HttpUrl

from .stealth import create_new_stealth_context

TIMEOUT = 600

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Результат поиска в интернете"""
    title: str
    url: HttpUrl

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SearchResult):
            return False
        return self.url == other.url


class PageMeta(BaseModel):
    """Meta-данные страницы"""
    title: str
    description: str | None = None


async def wait_for_full_page_load(page: Page, timeout: int = TIMEOUT) -> None:
    """Ожидает полной загрузки страницы.

    :param page: Текущая страница.
    :param timeout: ...
    """
    await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    await page.wait_for_load_state("load", timeout=timeout)
    # Ожидание появления body и head
    await page.wait_for_selector("body", state="attached", timeout=timeout)
    await page.wait_for_selector("head", state="attached", timeout=timeout)
    # Проверяем наличие элементов через JavaScript
    await page.wait_for_function("""
            () => {
                // Проверяем head
                const head = document.head;
                const hasHead = !!head;

                // Проверяем body (даже если скрыт)
                const body = document.body;
                const hasBody = !!body;

                // Проверяем базовую структуру
                const hasHtml = !!document.documentElement;
                const hasDoctype = !!document.doctype;

                return hasHead && hasBody && hasHtml;
            }
        """, timeout=timeout)

    # Дополнительная проверка, что контент загружен
    await page.wait_for_function("""
            () => {
                const body = document.body;
                if (!body) return false;

                // Проверяем различными способами
                const checks = [
                    // Проверяем детей body
                    body.children.length > 0,
                    // Проверяем текстовый контент
                    body.textContent && body.textContent.trim().length > 0,
                    // Проверяем innerHTML
                    body.innerHTML && body.innerHTML.trim().length > 0,
                    // Проверяем готовность DOM
                    document.readyState === 'complete'
                ];

                // Достаточно одного true
                return checks.some(check => check === true);
            }
        """, timeout=timeout)


async def get_current_page(browser: Browser) -> Page:
    """Получает текущую страницу в браузере.

    :param browser: Playwright браузер.
    :return Текущая страница.
    """
    if not browser.contexts:
        """context = await browser.new_context()"""
        context = await create_new_stealth_context(browser)
        return await context.new_page()
    context = browser.contexts[0]
    if not context.pages:
        return await context.new_page()
    return context.pages[-1]


async def extract_page_text(page: Page) -> str:
    """Извлекает текст с текущей страницы.

    :param page: Текущая Playwright страница.
    :return Текстовый контент страницы.
    """
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    body = soup.find("body")
    if body is None:
        return ""
    return body.get_text(separator="\n", strip=True)


async def extract_page_meta(page: Page) -> PageMeta:
    """Извлекает мета-данные страницы

    :param page: Текущая Playwright страница.
    :return Извлечённые мета-данные страницы.
    """
    title = await page.title()
    description_element = await page.query_selector("meta[name='description']")
    if description_element is None:
        return PageMeta(title=title)
    description = await description_element.get_attribute("content")
    return PageMeta(title=title, description=description)


def websearch(query: str, max_results: int = 7) -> list[SearchResult]:
    """Поиск в интернете.

    :param query: Поисковый запрос.
    :param max_results: Максимальное количество результатов.
    :return Список из результатов поиска.
    """
    with DDGS as ddg:
        return [SearchResult.model_validate({
            "title": result["title"], "url": result["href"]
        }) for result in ddg.text(query, max_results=max_results)]
