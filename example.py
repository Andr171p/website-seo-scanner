import asyncio

from website_seo_scanner.services import get_site_report

url = "https://tyumen-soft.ru/"


async def main() -> None:
    site_report = await get_site_report(url)
    print(site_report)


asyncio.run(main())
