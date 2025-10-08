import random

from playwright.async_api import Browser, BrowserContext

from .scripts import CANVAS_SPOOFING_SCRIPT, FINGERPRINT_SPOOFING_SCRIPT, WEBGL_SPOOFING_SCRIPT

# Доступные версии chrome для настройки отпечатков браузера
CHROME_VERSIONS: tuple[str, ...] = (
    "120.0.0.0",
    "119.0.0.0",
    "118.0.0.0",
    "117.0.0.0",
    "116.0.0.0",
    "115.0.0.0",
    "114.0.0.0"
)
# Возможные устройства для создания правдоподобных отпечатков браузера
PLATFORMS: tuple[str, ...] = (
    "Windows NT 10.0; Win64; x64",
    "Windows NT 6.1; Win64; x64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "X11; Linux x86_64",
)
# Человеко-подобные разрешения экранов
SCREEN_RESOLUTIONS: tuple[dict[str, int], ...] = (
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
)
# Доступные языки для браузера
LANGUAGES: tuple[str, ...] = (
    "en-US,en;q=0.9",
    "ru-RU,ru;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
)


def generate_user_agent() -> str:
    """Генерирует пользователя-подробный User-agent заголовки

    :return Сгенерированный User-agent
    """
    return (
        f"Mozilla/5.0 ({random.choice(PLATFORMS)}) AppleWebKit/537.36 "  # noqa: S311
        f"(KHTML, like Gecko) Chrome/{random.choice(CHROME_VERSIONS)} Safari/537.36"  # noqa: S311
    )


def generate_screen_resolution() -> dict[str, int]:
    """Генерирует реалистичного разрешения экрана

    :return Разрешение экрана в формате width и height
    """
    return random.choice(SCREEN_RESOLUTIONS)  # noqa: S311


def generate_accept_language() -> str:
    return random.choice(LANGUAGES)  # noqa: S311


def generate_extra_http_headers() -> dict[str, str]:
    """Генерирует дополнительные заголовки

    :return сгенерированные заголовки
    """
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",  # noqa: E501
        "Accept-Language": generate_accept_language(),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "DNT": str(random.randint(0, 1)),  # noqa: S311
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


SCRIPTS: tuple[str, ...] = (
    CANVAS_SPOOFING_SCRIPT,
    FINGERPRINT_SPOOFING_SCRIPT
    % (
        "ru-RU", "ru", random.choice(PLATFORMS), random.choice([4, 8, 12, 16])  # noqa: S311
    ),
    WEBGL_SPOOFING_SCRIPT,
)


async def create_new_stealth_context(browser: Browser) -> BrowserContext:
    """Создаёт новый контекст для браузера с анти-детекцией ботов.

    :param browser: Текущий асинхронный playwright браузер.
    :return Новый сконфигурированный контекст.
    """
    screen_resolution = generate_screen_resolution()
    context = await browser.new_context(
        viewport=screen_resolution,
        screen=screen_resolution,
        user_agent=generate_user_agent(),
        accept_downloads=False,
        ignore_https_errors=True,
        java_script_enabled=True,
        has_touch=random.choice([True, False]),  # noqa: S311
        is_mobile=False,
        extra_http_headers=generate_extra_http_headers(),
    )
    for script in SCRIPTS:
        await context.add_init_script(script)
    return context
