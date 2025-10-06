from __future__ import annotations

from typing import Final

from collections import Counter
from enum import StrEnum

from playwright.async_api import Browser, Page
from pydantic import BaseModel, HttpUrl, NonNegativeFloat, NonNegativeInt

from .linting import IssueLevel, PageIssue, lint_page
from .nlp import compare_texts
from .performance import measure_page_rendering_time
from .utils import get_current_page

# Оптимальное время рендеринга страницы в секундах
OPTIMAL_PAGE_LOAD_TIME = 2.5
# Максимальное недопустимое время рендеринга страницы в секундах
MAX_PAGE_LOAD_TIME = 5
# Критические элементы на странице (для подсчета SEO очков)
CRITICAL_ELEMENTS: tuple[str, ...] = ("title", "meta", "h1")
# Максимальные штрафы по категориям
MAX_PENALTIES_BY_CATEGORY: Final[dict[str, int]] = {
    "title": 25,
    "meta": 20,
    "headings": 20,
    "images": 15,
    "semantic": 10,
}
# Вес для каждой из проблем
PENALTY_WEIGHTS: Final[dict[str, float]] = {
    IssueLevel.ERROR: 1.0,
    IssueLevel.WARNING: 0.5,
    IssueLevel.INFO: 0.2,
}
# Веса для различных компонентов SEO оценки
SEO_WEIGHTS: Final[dict[str, float]] = {
    "performance": 0.25,      # Производительность
    "content_quality": 0.35,  # Качество контента
    "technical_seo": 0.30,    # Техническое SEO
    "relevance": 0.10,        # Релевантность
}


class ReportStatus(StrEnum):
    """Статус отчета по странице"""
    GREAT = "great"                    # Отлично
    GOOD = "good"                      # Хорошо
    SATISFACTORILY = "satisfactorily"  # Удовлетворительно
    BAD = "bad"                        # Плохо
    CRITICAL = "critical"              # Критические проблемы


# Пороговые значения для статуса отчета по странице
STATUS_THRESHOLDS: Final[dict[ReportStatus, float]] = {
    ReportStatus.GREAT: 90.0,
    ReportStatus.GOOD: 75.0,
    ReportStatus.SATISFACTORILY: 60.0,
    ReportStatus.BAD: 40.0,
    # CRITICAL: < 40.0
}


class PageReport(BaseModel):
    """SEO отчет по странице"""
    url: HttpUrl
    rendering_time: NonNegativeFloat
    seo_score: NonNegativeFloat
    meta_relevance_score: NonNegativeFloat
    status: ReportStatus
    issues: list[PageIssue]
    errors: NonNegativeInt
    warnings: NonNegativeInt
    infos: NonNegativeInt


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


def calculate_performance_score(rendering_time: float) -> float:
    """Рассчитывает качество рендеринга страницы"""
    if rendering_time <= OPTIMAL_PAGE_LOAD_TIME:
        return 100.0
    if rendering_time >= MAX_PAGE_LOAD_TIME:
        return 0.0
    return 50.0


def calculate_content_quality_score(issues: list[PageIssue]) -> float:
    """Рассчитывает оценку качества контента"""
    base_score = 100.0
    penalties: dict[str, float] = {
        "title": 0.0,
        "meta": 0.0,
        "headings": 0.0,
        "images": 0.0,
        "semantic": 0.0,
    }
    for issue in issues:
        if issue.category not in penalties:
            continue
        penalty_weight = PENALTY_WEIGHTS[issue.level]
        max_penalty = MAX_PENALTIES_BY_CATEGORY.get(issue.category, 10)
        penalty_value = penalty_weight * (max_penalty / 5)
        penalties[issue.category] = min(penalties[issue.category] + penalty_value, max_penalty)
    total_penalty = sum(penalties.values())
    return max(0.0, base_score - total_penalty)


def calculate_technical_seo_score(issues: list[PageIssue]) -> float:
    """Рассчитывает процент качества SEO страницы по техническим ошибкам"""
    base_score = 100.0
    penalty = 0.0
    max_penalty = 70.0  # Максимально допустимый штраф
    for issue in issues:
        if issue.element in CRITICAL_ELEMENTS:
            if issue.level == IssueLevel.ERROR:
                penalty += 15
            elif issue.level == IssueLevel.WARNING:
                penalty += 7
            elif issue.level == IssueLevel.INFO:
                penalty += 3
        elif issue.level == IssueLevel.ERROR:
            penalty += 8
        elif issue.level == IssueLevel.WARNING:
            penalty += 4
        elif issue.level == IssueLevel.INFO:
            penalty += 1
    return max(30.0, base_score - min(penalty, max_penalty))


def calculate_page_seo_score(
        rendering_time: float,
        issues: list[PageIssue],
        meta_relevance_score: float,
) -> float:
    seo_score = (
        calculate_performance_score(rendering_time) * SEO_WEIGHTS["performance"] +
        calculate_content_quality_score(issues) * SEO_WEIGHTS["content_quality"] +
        calculate_technical_seo_score(issues) * SEO_WEIGHTS["technical_seo"] +
        meta_relevance_score * SEO_WEIGHTS["relevance"]
    )
    return round(seo_score, 2)


def determine_status(seo_score: float) -> ReportStatus:
    """Определяет статус отчета на основе SEO оценки."""
    if seo_score >= STATUS_THRESHOLDS[ReportStatus.GREAT]:
        return ReportStatus.GREAT
    if seo_score >= STATUS_THRESHOLDS[ReportStatus.GOOD]:
        return ReportStatus.GOOD
    if seo_score >= STATUS_THRESHOLDS[ReportStatus.SATISFACTORILY]:
        return ReportStatus.SATISFACTORILY
    if seo_score >= STATUS_THRESHOLDS[ReportStatus.BAD]:
        return ReportStatus.BAD
    return ReportStatus.CRITICAL


async def form_page_report(browser: Browser, url: str) -> PageReport:
    """Формирует отчет по странице сайта.

    :param browser: Текущее состояние Playwright браузера.
    :param url: URL страницы сайта по которой нужно сформировать ответ.
    :return Отчет по странице.
    """
    rendering_info = await measure_page_rendering_time(url)
    page = await get_current_page(browser)
    await page.goto(url)
    issues = await lint_page(page)
    meta_relevance_score = await get_meta_relevance_score(page)
    rendering_time = rendering_info.dom_content_loaded / 100
    seo_score = calculate_page_seo_score(rendering_time, issues, meta_relevance_score)
    issue_level_counts = Counter(issue.level for issue in issues)
    return PageReport(
        url=HttpUrl(url),
        rendering_time=rendering_time,
        seo_score=seo_score,
        meta_relevance_score=meta_relevance_score,
        status=determine_status(seo_score),
        issues=issues,
        errors=issue_level_counts[IssueLevel.ERROR],
        warnings=issue_level_counts[IssueLevel.WARNING],
        infos=issue_level_counts[IssueLevel.INFO],
    )
