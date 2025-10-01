from __future__ import annotations

from playwright.async_api import async_playwright
from pydantic import BaseModel

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
        dom_content_loaded: Время до полной загрузки HTML DOM в мс.
        load_event: Время до полной загрузки страницы со всеми ресурсами в мс.
        first_paint: Первое отображение элемента на экране в мс.
    """
    dom_content_loaded: int
    load_event: int
    first_paint: int


async def measure_page_rendering_time(url: str) -> PageRenderingInfo:
    """Измеряет скорость рендеринга страницы.

    :param url: URL адрес страницы.
    :return информация о рендеринге страницы.
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        response = await page.evaluate(JS_PERFORMANCE_SCRIPT)
        return PageRenderingInfo.model_validate(response)
