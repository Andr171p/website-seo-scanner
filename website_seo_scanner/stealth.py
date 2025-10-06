import random

from playwright.async_api import Browser, BrowserContext, Page

USER_AGENTS: tuple[str, ...] = (
    # Chrome на Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # noqa: E501
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",  # noqa: E501
    # Chrome на Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # noqa: E501
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
)
ACCEPT_LANGUAGES: tuple[str, ...] = (
    "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,ru;q=0.8",
    "ru,en;q=0.9,en-US;q=0.8",
)


async def bypass_detection(page: Page) -> None:
    """Обходит защиту от ботов которая скрывает контент."""
    # Запускаем перед переходом на страницу
    await page.add_init_script("""
        // Блокируем детекторы автоматизации
        Object.defineProperty(navigator, 'webdriver', { get: () => false });

        // Удаляем свойства Playwright
        delete navigator.__proto__.webdriver;

        // Обходим проверки на headless браузер
        window.chrome = { runtime: {} };

        // Эмулируем человеческое поведение
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru', 'en-US', 'en'],
        });
    """)

    # Переопределяем некоторые свойства
    await page.evaluate("""
        // Обходим проверки на размеры экрана
        Object.defineProperty(screen, 'width', { get: () => 1920 });
        Object.defineProperty(screen, 'height', { get: () => 1080 });

        // Обходим проверки на availability
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    """)


def humanize_headers() -> dict[str, str]:
    """Человеко-подобные заголовки"""
    return {
        "User-Agent": random.choice(USER_AGENTS),  # noqa: S311
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa: E501
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),  # noqa: S311
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "DNT": "1",
        "Priority": "u=0, i",
    }


async def new_stealth_context(browser: Browser) -> BrowserContext:
    """Создает скрытый контекст браузера."""
    headers = humanize_headers()
    return await browser.new_context(
        # Основные настройки
        user_agent=headers["User-Agent"],
        viewport={"width": 1920, "height": 1080},
        device_scale_factor=1,
        # Отключаем детектируемые функции
        has_touch=False,
        is_mobile=False,
        java_script_enabled=True,
        # Устанавливаем заголовки
        extra_http_headers=headers,
        # Настройки для обхода детекции
        bypass_csp=True,
        ignore_https_errors=False,
        # Эмуляция реального браузера
        screen={"width": 1920, "height": 1080},
    )
