import asyncio

from website_seo_scanner.services import get_site_pages

url = "https://tyumen-soft.ru/"


async def main() -> None:
    site_pages = await get_site_pages(url)
    for site_page in site_pages:
        print(site_page)


asyncio.run(main())
