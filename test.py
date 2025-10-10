import asyncio

from playwright.async_api import async_playwright

from website_seo_scanner.nlp import (
    extract_keywords_using_tfidf,
    find_optimal_clusters,
    get_semantic_clusters,
)
from website_seo_scanner.utils import extract_page_text

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"
url1 = "https://1c.ru/"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        text = await extract_page_text(page)
        await page.goto(url1)
        text1 = await extract_page_text(page)
        print(find_optimal_clusters([text, text1], max_features=5))
        print(get_semantic_clusters([text, text1]))


asyncio.run(main())
