import asyncio

from playwright.async_api import async_playwright

from website_seo_scanner.linting import lint_page_content

url = "http://www.diocon.ru/"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        issues = await lint_page_content(browser, url)
        for issue in issues:
            print(issue)


asyncio.run(main())
