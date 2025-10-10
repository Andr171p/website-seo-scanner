import asyncio

from playwright.async_api import async_playwright

from website_seo_scanner.nlp import extract_keywords_using_tfidf, preprocess_text
from website_seo_scanner.utils import extract_page_text

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"
url1 = "https://1c.ru/"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        text = await extract_page_text(page)
        preprocessed_text = preprocess_text(text)
        print(extract_keywords_using_tfidf(preprocessed_text))


asyncio.run(main())
