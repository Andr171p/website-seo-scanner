import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from website_seo_scanner.linting import lint_page
from website_seo_scanner.report import form_page_report
from website_seo_scanner.utils import get_current_page

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"
url1 = "https://tyumen.1cbit.ru/1csoft/1s-buhgalteria-snt/"
url2 = "https://tyumen-soft.ru/"
url3 = "https://v8.1c.ru/partners/ka/tyumenskaya_oblast/"


async def main() -> None:
    async with Stealth().use_async(async_playwright()) as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        report = await form_page_report(page, url)
        print(report.model_dump())


asyncio.run(main())
