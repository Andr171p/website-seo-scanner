from typing import Final

import re
from enum import StrEnum

from bs4 import BeautifulSoup
from playwright.async_api import Browser
from pydantic import BaseModel

from .utils import get_current_page

OPTIMAL_TITLE_LENGTH = 55
OPTIMAL_TITLE_DELTA = 10
SEMANTIC_TAGS: Final[list[str]] = [
    "header", "nav", "main", "article", "section", "aside", "footer"
]
MAX_META_DESCRIPTION_LENGTH = 160


class IssueLevel(StrEnum):
    """Возможные уровни проблемы"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PageIssue(BaseModel):
    """Проблема на странице"""
    level: IssueLevel
    message: str
    element: str


def check_title(soup: BeautifulSoup) -> list[PageIssue]:
    """Проверка тега <title>"""
    issues: list[PageIssue] = []
    tag = soup.find("title")
    if not tag:
        issues.append(PageIssue(
            level=IssueLevel.ERROR,
            message="Отсутсвует тэг <title>!",
            element="title"
        ))
    text = tag.get_text().strip()
    if not text:
        issues.append(PageIssue(
            level=IssueLevel.ERROR,
            message="Тег <title> пустой!",
            element="title"
        ))
    if len(text) < OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA:
        issues.append(PageIssue(
            level=IssueLevel.WARNING,
            message=f"""Title слишком короткий ({len(text)} символов)!
            Оптимальная длина от {OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA}
            до {OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA}.""",
            element="title"
        ))
    if len(text) > OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA:
        issues.append(PageIssue(
            level=IssueLevel.WARNING,
            message=f"""Title слишком длинный ({len(text)} символов)!
            Оптимальная длина от {OPTIMAL_TITLE_LENGTH - OPTIMAL_TITLE_DELTA}
            до {OPTIMAL_TITLE_LENGTH + OPTIMAL_TITLE_DELTA}.""",
            element="title"
        ))
    return issues


def check_meta_description(soup: BeautifulSoup) -> list[PageIssue]:
    """Проверка meta описания страницы"""
    issues: list[PageIssue] = []
    meta_description = soup.find("meta", attrs={"name": "description"})
    if not meta_description:
        issues.append(PageIssue(
            level=IssueLevel.ERROR,
            message="Отсутствует meta-описание",
            element="meta"
        ))
        return issues
    content = meta_description.get("content", "").strip()
    if not content:
        issues.append(PageIssue(
            level=IssueLevel.ERROR,
            message="Пустое meta-описание",
            element="meta"
        ))
    elif len(content) > MAX_META_DESCRIPTION_LENGTH:
        issues.append(PageIssue(
            level=IssueLevel.WARNING,
            message=f"Meta-описание слишком длинное ({len(content)} символов)! "
            f"Рекомендуется от 120 до 160 символов.",
            element="meta"
        ))
    return issues


def check_heading(soup: BeautifulSoup) -> list[PageIssue]:
    """Проверка структуры заголовков"""
    issues: list[PageIssue] = []
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 0:
        issues.append(PageIssue(
            level=IssueLevel.ERROR,
            message="Отсутствует тег H1",
            element="h1"
        ))
    elif len(h1_tags) > 1:
        issues.append(PageIssue(
            level=IssueLevel.WARNING,
            message=f"Найдено {len(h1_tags)} тегов H1. Рекомендуется только один H1 на страницу",
            element="h1"
        ))
    headings = soup.find_all(re.compile(r"^h[1-6]$"))
    last_level = 0
    for heading in headings:
        level = int(heading.name[1])
        if level > last_level + 1:
            issues.append(PageIssue(
                level=IssueLevel.WARNING,
                message=f"Нарушена иерархия заголовков: H{level} после H{last_level}",
                element=heading.name
            ))
        last_level = level
    return issues


def check_images(soup: BeautifulSoup) -> list[PageIssue]:
    """Проверка изображений"""
    issues: list[PageIssue] = []
    images = soup.find_all("img")
    for image in images:
        alt, src = image.get("alt", ""), image.get("src", "")
        if not alt:
            issues.append(PageIssue(
                level=IssueLevel.WARNING,
                message="Изображение без атрибута 'alt'",
                element="img"
            ))
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
            issues.append(PageIssue(
                level=IssueLevel.INFO,
                message="В названии файла изображения нет описания",
                element="img"
            ))
    return issues


def check_semantic_structure(soup: BeautifulSoup) -> list[PageIssue]:
    """Проверка семантической структуры"""
    issues: list[PageIssue] = []
    for semantic_tag in SEMANTIC_TAGS:
        elements = soup.find_all(semantic_tag)
        if not elements:
            issues.append(PageIssue(
                level=IssueLevel.INFO,
                message=f"Не используется сематический тег <{semantic_tag}>",
                element=semantic_tag
            ))
    return issues


async def lint_page_content(browser: Browser, url: str) -> list[PageIssue]:
    """Выполняет SEO линтинг страницы. Возвращает найденные ошибки.

    :param browser: Объект Playwright браузера.
    :param url: URL адрес страницы.
    :return Список найденных SEO ошибок страницы.
    """
    page = await get_current_page(browser)
    await page.goto(url)
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    return [
        *check_title(soup),
        *check_meta_description(soup),
        *check_heading(soup),
        *check_images(soup),
        *check_semantic_structure(soup)
    ]
