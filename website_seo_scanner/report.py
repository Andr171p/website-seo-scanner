from __future__ import annotations

from enum import StrEnum

from playwright.async_api import Browser, Page
from pydantic import BaseModel, HttpUrl, NonNegativeFloat, NonNegativeInt

from .linting import PageIssue, lint_page
from .nlp import compare_texts
from .performance import measure_page_rendering_time
from .utils import get_current_page


class ReportStatus(StrEnum):
    """Статус отчета по странице"""
    GREAT = "great"                    # Отлично
    GOOD = "good"                      # Хорошо
    SATISFACTORILY = "satisfactorily"  # Удовлетворительно
    BAD = "bad"                        # Плохо
    CRITICAL = "critical"              # Критические проблемы


class PageReport(BaseModel):
    """SEO отчет по странице"""
    url: HttpUrl
    rendering_time: NonNegativeInt
    seo_score: NonNegativeFloat
    meta_relevance_score: NonNegativeFloat
    status: ReportStatus
    issues: list[PageIssue]
    errors: NonNegativeInt
    warnings: NonNegativeInt
    infos: NonNegativeInt


async def get_meta_relevance_score(page: Page) -> float:
    """Получает оценку релевантности meta-описания и контента на странице"""
    meta_description = await page.evaluate("""() => {
        const meta = document.querySelector('meta[name="description"]');
        return meta ? meta.content : null;
    }""")
    content = await page.locator("body").inner_text()
    similarity_score = compare_texts(meta_description, content)
    return round(similarity_score, 2)


def calculate_seo_score(
        rendering_time: int,
        issues: list[PageIssue]
) -> float: ...


async def form_page_report(browser: Browser, url: str) -> PageReport:
    rendering_info = await measure_page_rendering_time(url)
    page = await get_current_page(browser)
    await page.goto(url)
    issues = await lint_page(page)
    meta_relevance_score = await get_meta_relevance_score(page)
    seo_score = calculate_seo_score(rendering_info.dom_content_loaded, issues)
