from typing import Final

import logging
import re
from enum import StrEnum

from bs4 import BeautifulSoup
from playwright.async_api import Page
from pydantic import BaseModel

from .nlp import compare_texts

OPTIMAL_TITLE_LENGTH = 55
OPTIMAL_TITLE_DELTA = 10
SEMANTIC_TAGS: Final[list[str]] = [
    "header", "nav", "main", "article", "section", "aside", "footer"
]
MAX_META_DESCRIPTION_LENGTH = 160
MIN_META_DESCRIPTION_LENGTH = 120
SHORT_RELEVANCE_SCORE, CRITICAL_RELEVANCE_SCORE = 0.5, 0.3
GREAT_SEMANTIC_TAG_COUNT = 4

logger = logging.getLogger(__name__)


class FindingLevel(StrEnum):
    """Возможные уровни проблемы"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    OPTIMAL = "optimal"
    GOOD = "good"
    GREAT = "great"


class PageFinding(BaseModel):
    """Проблема на странице"""
    level: FindingLevel
    message: str
    category: str
    element: str


def check_title(soup: BeautifulSoup) -> list[PageFinding]:
    """Проверка тега <title>"""
    findings: list[PageFinding] = []
    tag = soup.find("title")
    if not tag:
        return [PageFinding(
            level=FindingLevel.CRITICAL,
            message="Отсутсвует тэг <title>!",
            category="title",
            element="title"
        )]
    text = tag.get_text().strip()
    if not text:
        return [PageFinding(
            level=FindingLevel.CRITICAL,
            message="Тег <title> пустой!",
            category="title",
            element="title"
        )]
    if len(text) < OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message=f"""Title слишком короткий ({len(text)} символов)!
            Оптимальная длина от {OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA}
            до {OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA}.""",
            category="title",
            element="title"
        ))
    elif len(text) > OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message=f"""Title слишком длинный ({len(text)} символов)!
            Оптимальная длина от {OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA}
            до {OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA}.""",
            category="title",
            element="title"
        ))
    else:
        findings.append(PageFinding(
            level=FindingLevel.OPTIMAL,
            message=f"Оптимальная длина title ({len(text)} символов)",
            category="title",
            element="title"
        ))
    return findings


def check_meta_description(soup: BeautifulSoup) -> list[PageFinding]:
    """Проверка meta описания страницы"""
    findings: list[PageFinding] = []
    meta_description = soup.find("meta", attrs={"name": "description"})
    if not meta_description:
        return [PageFinding(
            level=FindingLevel.CRITICAL,
            message="Отсутствует meta-описание",
            category="meta",
            element="meta"
        )]
    content = meta_description.get("content", "").strip()
    if not content:
        return [PageFinding(
            level=FindingLevel.CRITICAL,
            message="Пустое meta-описание",
            category="meta",
            element="meta"
        )]
    if len(content) > MAX_META_DESCRIPTION_LENGTH:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message=f"Meta-описание слишком длинное ({len(content)} символов)! "
            f"Рекомендуемая длина от {MIN_META_DESCRIPTION_LENGTH} "
            f"до {MAX_META_DESCRIPTION_LENGTH} символов.",
            category="meta",
            element="meta"
        ))
    elif MIN_META_DESCRIPTION_LENGTH <= len(content) <= MIN_META_DESCRIPTION_LENGTH:
        findings.append(PageFinding(
            level=FindingLevel.OPTIMAL,
            message=f"Оптимальная длина meta-описания ({len(content)} символов)",
            category="meta",
            element="meta"
        ))
    else:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message=f"Meta-описание слишком короткое ({len(content)} символов)! "
            f"Рекомендуемая длина от {MIN_META_DESCRIPTION_LENGTH} "
            f"до {MAX_META_DESCRIPTION_LENGTH}",
            category="meta",
            element="meta"
        ))
    return findings


def check_heading(soup: BeautifulSoup) -> list[PageFinding]:
    """Проверка структуры заголовков"""
    findings: list[PageFinding] = []
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        findings.append(PageFinding(
            level=FindingLevel.CRITICAL,
            message="Отсутствует тег H1",
            category="heading",
            element="h1"
        ))
    elif len(h1_tags) > 1:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message=f"Найдено {len(h1_tags)} тегов H1. Рекомендуется только один H1 на страницу",
            category="heading",
            element="h1"
        ))
    elif len(h1_tags) == 1:
        findings.append(PageFinding(
            level=FindingLevel.OPTIMAL,
            message="Оптимальное количество H1 тегов (ровно 1)",
            category="heading",
            element="h1"
        ))
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    last_level = 0
    hierarchy_correct = True
    for heading in headings:
        level = int(heading.name[1])
        if level > last_level + 1:
            findings.append(PageFinding(
                level=FindingLevel.WARNING,
                message=f"Нарушена иерархия заголовков: H{level} после H{last_level}",
                category="heading",
                element=heading.name
            ))
            hierarchy_correct = False
        last_level = level
    if hierarchy_correct:
        findings.append(PageFinding(
            level=FindingLevel.GREAT,
            message="Правильная иерархия заголовков",
            category="heading",
            element=f"h1-h{last_level}"
        ))
    return findings


def check_images(soup: BeautifulSoup) -> list[PageFinding]:
    """Проверка изображений"""
    findings: list[PageFinding] = []
    images = soup.find_all("img")
    if not images:
        return [PageFinding(
            level=FindingLevel.INFO,
            message="На странице нет изображений",
            category="image",
            element="img"
        )]
    images_with_alt = 0  # Количество изображений с описанием
    images_without_description = 0  # Изображения без описания
    for image in images:
        alt, src = image.get("alt", ""), image.get("src", "")
        if not alt:
            findings.append(PageFinding(
                level=FindingLevel.WARNING,
                message="Изображение без атрибута 'alt'",
                category="image",
                element="img"
            ))
        else:
            images_with_alt += 1
        if (
                (src and any(
                    type in src.lower()
                    for type in ["image", "img", "picture"])  # noqa: A001
                )
                and not any(
                    extension in src.lower()
                    for extension in [".jpg", ".jpeg", ".png", ".webp"]
            )
        ):
            images_without_description += 1
    if images_without_description > 0:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message=f"В названии файлов {images_without_description}"
            " изображений нет описания!",
            category="image",
            element="img"
        ))
    return findings


def check_semantic_structure(soup: BeautifulSoup) -> list[PageFinding]:
    """Проверка семантической структуры"""
    findings: list[PageFinding] = []
    used_semantic_tags: list[str] = []
    for semantic_tag in SEMANTIC_TAGS:
        elements = soup.find_all(semantic_tag)
        if not elements:
            findings.append(PageFinding(
                level=FindingLevel.INFO,
                message=f"Не используется сематический тег <{semantic_tag}>",
                category="semantic",
                element=semantic_tag
            ))
        else:
            used_semantic_tags.append(semantic_tag)
    if used_semantic_tags:
        findings.append(PageFinding(
            level=FindingLevel.GOOD,
            message=f"Используются семантические теги: {', '.join(used_semantic_tags)}",
            category="semantic",
            element=";".join(used_semantic_tags)
        ))
    if len(used_semantic_tags) > GREAT_SEMANTIC_TAG_COUNT:
        findings.append(PageFinding(
            level=FindingLevel.GREAT,
            message="Отличное использование семантической разметки",
            category="semantic",
            element=";".join(used_semantic_tags)
        ))
    return findings


def check_meta_and_content_similarity(soup: BeautifulSoup) -> list[PageFinding]:
    """Проверяет сематическое соответствие между meta-описанием и контентом на странице"""
    findings: list[PageFinding] = []
    meta_description = soup.find("meta", attrs={"name": "description"})
    if not meta_description:
        return findings
    content = meta_description.get("content", "").strip()
    body = soup.find("body")
    if body is None:
        return [PageFinding(
            level=FindingLevel.CRITICAL,
            message="Страница с пустым контентом",
            category="semantic",
            element="body"
        )]
    text = body.get_text(separator="\n", strip=True)
    similarity_score = compare_texts(content, text)
    if CRITICAL_RELEVANCE_SCORE < similarity_score < SHORT_RELEVANCE_SCORE:
        findings.append(PageFinding(
            level=FindingLevel.INFO,
            message="Соответствие meta-описания к контенту страницы, "
            f"Релевантность: {similarity_score * 100:.1f}%",
            category="semantic",
            element="body"
        ))
    elif similarity_score <= CRITICAL_RELEVANCE_SCORE:
        findings.append(PageFinding(
            level=FindingLevel.WARNING,
            message="Низкое соответствие meta-описания к контенту страницы, "
            f"Релевантность: {similarity_score * 100:.1f}%",
            category="semantic",
            element="body"
        ))
    else:
        findings.append(PageFinding(
            level=FindingLevel.GREAT,
            message="Высокое описание meta-описания к контенту страницы "
            f"Релевантность: ({similarity_score * 100:.1f}%)",
            category="semantic",
            element="body"
        ))
    return findings


async def lint_page(page: Page) -> list[PageFinding]:
    """Выполняет SEO линтинг страницы. Возвращает найденные ошибки.

    :param page: Объект Playwright страницы.
    :return Список найденных SEO замечаний страницы.
    """
    await page.wait_for_selector("body:not(:empty)")
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    return [
        *check_title(soup),
        *check_meta_description(soup),
        *check_heading(soup),
        *check_images(soup),
        *check_semantic_structure(soup),
        *check_meta_and_content_similarity(soup),
    ]
