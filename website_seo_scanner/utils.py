import logging

from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page

from .stealth import create_new_stealth_context

TIMEOUT = 600

logger = logging.getLogger(__name__)


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
