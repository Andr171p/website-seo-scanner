import asyncio

from playwright.async_api import async_playwright

from website_seo_scanner.linting import lint_page
from website_seo_scanner.performance import measure_page_rendering_time
from website_seo_scanner.schemas import SitePage
from website_seo_scanner.utils import extract_page_meta, extract_page_text

url = "https://tyumen-soft.ru/"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        rendering_info = await measure_page_rendering_time(page, url)
        meta = await extract_page_meta(page)
        text = await extract_page_text(page)
        findings = await lint_page(page)
        site_page = SitePage(
            url=url,
            meta=meta,
            text=text,
            findings=findings,
            rendering_time=rendering_info.dom_content_loaded / 1000,
        )
        print(site_page)


asyncio.run(main())
