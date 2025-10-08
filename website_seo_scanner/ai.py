from pydantic import HttpUrl

from .tree import TreeNode


def select_target_pages(tree: TreeNode) -> list[HttpUrl]:
    """Выделяет ключевые страницы сайта для SEO анализа

    :param tree: Дерево сайта.
    :return URL адреса страниц.
    """
    target_urls: list[HttpUrl] = [tree.url, tree.last_changed_node().url]
    for node in tree.iter_nodes():
        if node.is_leaf:
            continue
    return target_urls
