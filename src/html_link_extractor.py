"""HTML 链接提取器 — 下载网页提取所有链接。"""

import re
import urllib.request
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin


class LinkExtractor(HTMLParser):
    """提取页面中所有 <a href> 和 <img src> 链接。"""

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a":
            href = attrs_dict.get("href")
            if href:
                self.links.append({
                    "type": "hyperlink",
                    "url": urljoin(self.base_url, href),
                    "text": "",
                })
        elif tag == "img":
            src = attrs_dict.get("src")
            if src:
                self.links.append({
                    "type": "image",
                    "url": urljoin(self.base_url, src),
                })


def extract_links(url: str) -> list[dict[str, str]]:
    print(f"Fetching: {url}")
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Failed: {e}")
        return []

    parser = LinkExtractor(url)
    parser.feed(html)

    # 按类型统计
    counts: dict[str, int] = {}
    for link in parser.links:
        counts[link["type"]] = counts.get(link["type"], 0) + 1

    print(f"  Found {len(parser.links)} links:")
    for t, c in sorted(counts.items()):
        print(f"    {t}: {c}")

    return parser.links


if __name__ == "__main__":
    links = extract_links("https://httpbin.org/links/10")
    for link in links[:5]:
        print(f"  {link['type']}: {link['url']}")
