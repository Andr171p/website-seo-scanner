from website_seo_scanner.tree import build_site_tree

tree = build_site_tree("https://tyumen.1cbit.ru/")
k = 0
for node in tree.iter_nodes():
    if node.is_leaf:
        continue
    print(node)
    k += 1


print(k)
