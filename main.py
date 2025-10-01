from website_seo_scanner.tree import build_site_tree

url = "https://1c.ru/"

tree = build_site_tree(url)

print(tree.to_string())
print(tree.max_depth())
print(tree.count_nodes())
