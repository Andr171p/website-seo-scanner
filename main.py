import asyncio

from playwright.async_api import async_playwright

from website_seo_scanner.linting import lint_page
from website_seo_scanner.report import form_page_report
from website_seo_scanner.utils import get_current_page

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        report = await form_page_report(browser, url)
        print(report)


asyncio.run(main())
