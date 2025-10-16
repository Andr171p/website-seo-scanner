from playwright.async_api import async_playwright
from pydantic import HttpUrl

from .linting import lint_page
from .performance import measure_page_rendering_time
from .schemas import PageReport, SiteReport
from .tree import PRIORITY_KEYWORDS, build_site_tree, extract_key_pages
from .utils import extract_page_meta, iter_pages


async def get_site_report(url: HttpUrl) -> SiteReport:
    tree = build_site_tree(url)
    urls = extract_key_pages(tree, list(PRIORITY_KEYWORDS), max_result=15)
    page_reports: list[PageReport] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        async for page in iter_pages(browser, urls):
            rendering_info = await measure_page_rendering_time(page, page.url)
            findings = await lint_page(page)
            meta = await extract_page_meta(page)
            page_reports.append(PageReport(
                url=HttpUrl(page.url),
                meta=meta,
                findings=findings,
                rendering_time=rendering_info.dom_content_loaded / 100
            ))
    return SiteReport(base_url=url, pages=page_reports)
