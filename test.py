from website_seo_scanner.tree import build_site_tree, extract_key_pages

tree = build_site_tree("https://tyumen.1cbit.ru/")

print(tree.to_string())

