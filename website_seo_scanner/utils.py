from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page


async def get_current_page(browser: Browser) -> Page:
    """Получает текущую страницу в браузере.

    :param browser: Playwright браузер.
    :return Текущая страница.
    """
    if not browser.contexts:
        context = await browser.new_context()
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
