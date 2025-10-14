from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, HttpUrl, NonNegativeFloat, NonNegativeInt


class PageMeta(BaseModel):
    """Мета-данные страницы"""
    title: str
    description: str


class SitePage(BaseModel):
    """Страница сайта.

    Attributes:
        url: URL адрес страницы.
        meta: Meta-данные страницы (нужные для SEO продвижения).
        text: Отчищенный текстовый контент страницы.
    """
    url: HttpUrl
    meta: PageMeta
    text: str
    findings: list[PageFinding]
    rendering_time: float


class Site(BaseModel):
    domain: str
    pages: list[SitePage]


class AboutSite(BaseModel):
    """Информация о сайте

    Attributes:
        url: Адрес сайта.
        title: Название компании/сайта.
        description: Описание компании/сайта.
        industry: Отрасль или ниша.
        target_audience: Целевая аудитория.
        target_location: Целевой регион или город.
        main_products: Основные продукты, услуги и.т.д компании.
        key_features: Ключевые преимущества.
    """
    url: HttpUrl
    title: str
    description: str
    industry: str
    target_audience: str
    target_location: str
    main_products: list[str]
    key_features: list[str]


class FindingLevel(StrEnum):
    """Уровни значимости замечания"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    OPTIMAL = "optimal"
    GOOD = "good"
    GREAT = "great"


class PageFinding(BaseModel):
    """Проблема на странице

    Attributes:
        level: Значимость замечания.
        message: Человеко-читаемое сообщение.
        category: Категория к которой относится замечание, например: 'heading', 'title', ...
        element: Элемент страницы к которому относится замечание.
    """
    level: FindingLevel
    message: str
    category: str
    element: str


class ReportLevels(BaseModel):
    """Распределения количества замечаний по уровням значимости"""
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
