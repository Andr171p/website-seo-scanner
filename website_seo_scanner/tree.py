"""Модуль для построения дерева структуры сайта"""

from __future__ import annotations

import random
from collections.abc import Iterator
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl
from usp.objects.page import SitemapPage
from usp.tree import sitemap_tree_for_homepage

PRIORITY_KEYWORDS: tuple[str, ...] = (
    "product",
    "services",
    "catalog",
    "category",
    "shop",
    "blog",
    "article",
    "news",
    "post",
    "about",
    "contact",
    "price",
    "buy",
    "order",
    "cases",
)


def parse_url_path(url: str) -> list[str]:
    """Разбивает URL на части.

    Пример: "http://site.com/folder/page" -> ["folder", "page"]
    """
    path = urlparse(url).path
    return [segment for segment in path.strip("/").split("/") if segment]


class TreeNode(BaseModel):
    """Узел дерева структуры страниц сайта"""
    name: str
    url: HttpUrl
    priority: float | None = None
    last_modified: datetime | None = None
    children: list[TreeNode] = Field(default_factory=list)

    @property
    def sections(self) -> list[str]:
        """Секции внутри которых находится страница"""
        url = str(self.url)
        domain = urlparse(url).netloc
        url = (
            url
            .replace(domain, "")
            .replace("http://", "")
            .replace("https://", "")
        )
        return url.split("/")

    @property
    def is_leaf(self) -> bool:
        """Является ли узел листом"""
        return len(self.children) == 0

    def max_depth(self) -> int:
        """Максимальная глубина дерева"""
        if not self.children:
            return 0
        return max(child.max_depth() for child in self.children) + 1

    def count_nodes(self) -> int:
        """Подсчитывает общее количество узлов в дереве"""
        count = 1
        for child in self.children:
            count += child.count_nodes()
        return count

    def iter_nodes(self) -> Iterator[TreeNode]:
        """Итерация по всем узлам дерева"""
        yield self
        for child in self.children:
            yield from child.iter_nodes()

    def iter_leaves(self) -> Iterator[TreeNode]:
        """Итерация по листьям дерева"""
        for node in self.iter_nodes():
            if node.is_leaf:
                yield node

    def find_node(self, url: str) -> TreeNode | None:
        """Рекурсивный поиск страницы по её URL"""
        if self.url == url:
            return self
        for child in self.children:
            found = child.find_node(url)
            if found:
                return found
        return None

    def to_string(self, max_depth: int | None = None) -> str:
        """Представление дерева в человеко-читаемом формате"""
        lines: list[str] = []
        self.draw_tree_lines(lines, max_depth=max_depth)
        return "\n".join(lines)

    def draw_tree_lines(
            self,
            lines: list[str],
            max_depth: int | None = None,
            current_depth: int = 0,
            prefix: str = "",
            is_last: bool = True,
    ) -> None:
        """Формирует строковое представление для отображения дерева"""
        if max_depth is not None and current_depth >= max_depth:
            return
        meta_parts: list[str] = []
        if self.priority is not None:
            meta_parts.append(f"Приоритет: {self.priority}")
        if self.last_modified:
            meta_parts.append(f"Последнее изменение: {self.last_modified.strftime("%d.%m.%Y")}")
        meta_str = " [" + ", ".join(meta_parts) + "]" if meta_parts else ""
        if current_depth == 0:
            icon = "🌐"
            line = f"{icon} {self.name} ({self.url}){meta_str}"
            lines.append(line)
        else:
            icon = "📄" if self.is_leaf else "📁"
            connector = "└── " if is_last else "├── "
            line = f"{prefix}{connector}{icon} {self.name}{meta_str}"
            lines.append(line)
        new_prefix = prefix if current_depth == 0 else prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(self.children):
            is_last_child = (i == len(self.children) - 1)
            child.draw_tree_lines(
                lines, max_depth, current_depth + 1, new_prefix, is_last_child
            )

    def last_site_change(self) -> datetime | None:
        """Последнее изменение на сайте"""
        latest = self.last_modified
        for node in self.iter_nodes():
            if node.last_modified and (latest is None or node.last_modified > latest):
                latest = node.last_modified
        return latest

    def last_changed_node(self) -> TreeNode:
        """Последняя изменённая страница"""
        latest_node = self
        for node in self.iter_nodes():
            if node.last_modified and \
                    (latest_node is None or node.last_modified > latest_node.last_modified):
                latest_node = node
        return latest_node

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TreeNode):
            return False
        return self.url == other.url


def add_page_to_tree(
        base_url: str,
        root: TreeNode,
        page: SitemapPage,
        segments: list[str],
        current_depth: int = 0
) -> None:
    if current_depth >= len(segments):
        return
    current_segment = segments[current_depth]
    node: TreeNode | None = next(
        (child for child in root.children if child.name == current_segment), None
    )
    if node is None:
        path_part = "/".join(segments[:current_depth + 1])
        full_url = f"{base_url.rstrip("/")}/{path_part}"
        node = TreeNode.model_validate({
            "name": current_segment,
            "url": full_url,
            "priority": page.priority,
            "last_modified": page.last_modified,
        })
        root.children.append(node)
    add_page_to_tree(base_url, node, page, segments, current_depth + 1)


def build_site_tree(url: str) -> TreeNode:
    """Рекурсивно строит дерево сайта по страницам из sitemap.xml.

    :param url: URL адрес сайта.
    :return Построенное дерево структуры сайта.
    """
    name = (
        url
        .replace("http://", "")
        .replace("https://", "")
        .replace("/", "")
    )
    root = TreeNode(name=name, url=HttpUrl(url))
    sitemap = sitemap_tree_for_homepage(url, use_robots=False)
    for page in sitemap.all_pages():
        segments = parse_url_path(page.url)
        add_page_to_tree(url, root, page, segments)
    return root


def extract_key_pages(tree: TreeNode, max_result: int = 15) -> set[HttpUrl]:
    """Извлекает URL ключевых страниц сайта.

    :param tree: Дерево сайта.
    :param max_result: Максимальное количество извлекаемых страниц.
    """
    key_pages: set[HttpUrl] = {tree.url, tree.last_changed_node()}  # Первые ключевые страницы
    for node in tree.iter_nodes():
        if any(
                priority_keyword in str(node.url).lower() for priority_keyword in PRIORITY_KEYWORDS
        ):
            key_pages.add(random.choice(node.children))  # noqa: S311
    return key_pages[::max_result]
