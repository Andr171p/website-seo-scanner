from playwright.async_api import Browser, Page


async def get_current_page(browser: Browser) -> Page:
    """Получает текущую страницу в браузере"""
    if not browser.contexts:
        context = await browser.new_context()
        return await context.new_page()
    context = browser.contexts[0]
    if not context.pages:
        return await context.new_page()
    return context.pages[-1]
