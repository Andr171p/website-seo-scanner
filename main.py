import asyncio

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from website_seo_scanner.linting import lint_page
from website_seo_scanner.utils import get_current_page

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        issues = await lint_page(page)
        for issue in issues:
            print(issue)


asyncio.run(main())
