import logging

from playwright.async_api import Page
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# JS скрипт для анализа производительности рендеринга страницы
JS_PERFORMANCE_SCRIPT = """
() => {
    const perf = window.performance;
    const timing = perf.timing;

    return {
        'dom_content_loaded': timing.domContentLoadedEventEnd - timing.navigationStart,
        'load_event': timing.loadEventEnd - timing.navigationStart,
        'first_paint': perf.getEntriesByName('first-paint')[0]?.startTime || 0,
        'first_contentful_paint': perf.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
        'largest_contentful_paint': perf.getEntriesByType('largest-contentful-paint')[0]?.renderTime || 0,
        'cumulative_layout_shift': perf.getEntriesByType('layout-shift').reduce((sum, entry) => sum + entry.value, 0)
    };
}
"""  # noqa: E501
# Таймаут по умолчанию в секундах
TIMEOUT = 10


class PageRenderingInfo(BaseModel):
    """Информация с метриками по загрузке страницы.

    Attributes:
        dom_content_loaded: Время до полной загрузки HTML DOM в ms.
        load_event: Время до полной загрузки страницы со всеми ресурсами в мс.
        first_paint: Первое отображение элемента на экране в мс.
    """
    dom_content_loaded: float
    load_event: float
    first_paint: float


async def measure_page_rendering_time(page: Page, url: str) -> PageRenderingInfo:
    """Измеряет скорость рендеринга страницы.
`
    :param page: Текущая playwright страница.
    :param url: URL адрес страницы.
    :return информация о рендеринге страницы.
    """
    await page.goto(url, wait_until="domcontentloaded")
    response = await page.evaluate(JS_PERFORMANCE_SCRIPT)
    logger.info("Measured rendering time of page %s", url, extra=response)
    return PageRenderingInfo.model_validate(response)
