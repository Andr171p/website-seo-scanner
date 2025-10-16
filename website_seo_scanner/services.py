from playwright.async_api import async_playwright
from pydantic import HttpUrl

from .linting import lint_page
from .performance import measure_page_rendering_time
from .schemas import PageContent, SitePage
from .tree import PRIORITY_KEYWORDS, build_site_tree, extract_key_pages
from .utils import extract_page_meta, extract_page_text, iter_pages


async def get_site_pages(url: HttpUrl) -> list[SitePage]:
    tree = build_site_tree(url)
    urls = extract_key_pages(tree, list(PRIORITY_KEYWORDS), max_result=15)
    site_pages: list[SitePage] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        async for page in iter_pages(browser, urls):
            rendering_info = await measure_page_rendering_time(page, page.url)
            findings = await lint_page(page)
            meta = await extract_page_meta(page)
            text = await extract_page_text(page)
            site_pages.append(SitePage(
                url=HttpUrl(page.url),
                rendering_time=rendering_info.dom_content_loaded / 100,
                findings=findings,
                content=PageContent(meta=meta, text=text),
            ))
    return site_pages
