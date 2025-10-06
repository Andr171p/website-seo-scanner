import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from website_seo_scanner.linting import lint_page
from website_seo_scanner.report import form_page_report
from website_seo_scanner.utils import get_current_page

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"
url1 = "https://tyumen.1cbit.ru/"
url2 = "https://tyumen-soft.ru/"


async def main() -> None:
    async with Stealth().use_async(async_playwright()) as playwright:
        browser = await playwright.chromium.launch(headless=False)
        report = await form_page_report(browser, url1)
        print(report)


asyncio.run(main())
