from website_seo_scanner.tree import PRIORITY_KEYWORDS, build_site_tree, extract_key_pages

tree = build_site_tree("https://tyumen-soft.ru/")

key_pages = extract_key_pages(tree, list(PRIORITY_KEYWORDS), max_result=15)

print(key_pages)
