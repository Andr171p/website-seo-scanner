import asyncio

from playwright.async_api import async_playwright

from website_seo_scanner.report import form_page_report
from website_seo_scanner.utils import get_current_page

url = "http://www.diocon.ru/introduction/borovskaya-ptitsefabrika/"
url1 = "https://tyumen.1cbit.ru"
url2 = "https://tyumen-soft.ru/"
url3 = "https://v8.1c.ru/partners/ka/tyumenskaya_oblast/"
url4 = "https://wiseadvice.ru/"
test_url = "https://www.browserscan.net/bot-detection"


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor,AudioServiceOutOfProcess",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-ipc-flooding-protection",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-translate",
                "--disable-extensions",
                "--disable-component-extensions-with-background-pages",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-client-side-phishing-detection",
                "--disable-crash-reporter",
                "--disable-oopr-debug-crash-dump",
                "--no-crash-upload",
                "--disable-breakpad",
                "--disable-component-update",
                "--disable-domain-reliability",
                "--disable-sync",
                "--disable-software-rasterizer",
                "--force-color-profile=srgb",
                "--metrics-recording-only",
                "--disable-default-apps",
                "--mute-audio",
            ]
        )
        page = await get_current_page(browser)
        """await page.goto(test_url)
        await asyncio.sleep(25)"""
        report = await form_page_report(page, url2)
        print(report.model_dump())


asyncio.run(main())
