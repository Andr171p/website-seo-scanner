from __future__ import annotations

from collections import Counter

from playwright.async_api import Page
from pydantic import BaseModel, HttpUrl, NonNegativeFloat, NonNegativeInt

from .linting import FindingLevel, PageFinding, lint_page
from .nlp import compare_texts
from .performance import measure_page_rendering_time

# Оптимальное время рендеринга страницы в секундах
OPTIMAL_PAGE_LOAD_TIME = 2.5
# Максимальное недопустимое время рендеринга страницы в секундах
MAX_PAGE_LOAD_TIME = 5


class ReportLevels(BaseModel):
    critical: NonNegativeInt
    errors: NonNegativeInt
    warnings: NonNegativeInt
    infos: NonNegativeInt
    good: NonNegativeInt
    great: NonNegativeInt


class PageReport(BaseModel):
    """SEO отчет по странице"""
    url: HttpUrl
    rendering_time: NonNegativeFloat
    meta_relevance_score: NonNegativeFloat
    findings: list[PageFinding]
    levels: ReportLevels


async def get_meta_relevance_score(page: Page) -> float:
    """Получает оценку релевантности meta-описания и контента на странице

    :param page: Текущая Playwright страница.
    :return Процент соотношения meta-описания к содержанию контента.
    """
    meta_description = await page.evaluate("""() => {
        const meta = document.querySelector('meta[name="description"]');
        return meta ? meta.content : null;
    }""")
    content = await page.locator("body").inner_text()
    similarity_score = compare_texts(meta_description, content)
    return round(similarity_score, 2) * 100


async def form_page_report(page: Page, url: str) -> PageReport:
    """Формирует отчет по странице сайта.

    :param page: Текущая Playwright страница.
    :param url: URL страницы сайта по которой нужно сформировать отчет.
    :return Отчет по странице.
    """
    rendering_info = await measure_page_rendering_time(page, url)
    findings = await lint_page(page)
    meta_relevance_score = await get_meta_relevance_score(page)
    rendering_time = rendering_info.dom_content_loaded / 1000
    finding_level_counts = Counter(finding.level for finding in findings)
    return PageReport(
        url=HttpUrl(url),
        rendering_time=rendering_time,
        meta_relevance_score=meta_relevance_score,
        findings=findings,
        levels=ReportLevels(
            critical=finding_level_counts[FindingLevel.CRITICAL],
            errors=finding_level_counts[FindingLevel.ERROR],
            warnings=finding_level_counts[FindingLevel.WARNING],
            infos=finding_level_counts[FindingLevel.INFO],
            good=finding_level_counts[FindingLevel.GOOD],
            great=finding_level_counts[FindingLevel.GREAT],
        )
    )
