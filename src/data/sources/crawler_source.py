import re
from typing import Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def _clean_text(value: str) -> str:
    return " ".join((value or "").split())


def _extract_date(text: str) -> str:
    match = re.search(r"(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2})", text or "")
    return match.group(1).replace("/", "-").replace(".", "-") if match else ""


def fetch_crawler(config: Dict) -> List[Dict]:
    """从网页抓取资讯。"""
    url = config.get("url", "")
    if not url:
        return []

    response = requests.get(
        url,
        timeout=int(config.get("timeout", 15)),
        headers={
            "User-Agent": config.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
        },
    )
    response.encoding = config.get("encoding", response.apparent_encoding)
    soup = BeautifulSoup(response.text, "html.parser")

    mode = config.get("mode", "selector")
    if mode == "anchor_list":
        return _fetch_anchor_list(soup, config)
    return _fetch_by_selector(soup, config)


def _fetch_by_selector(soup: BeautifulSoup, config: Dict) -> List[Dict]:
    selector = config.get("selector", "")
    title_sel = config.get("title_sel", "h3")
    content_sel = config.get("content_sel", "p")
    link_sel = config.get("link_sel", "a")
    base_url = config.get("base_url", config.get("url", ""))
    max_items = int(config.get("max_items", 30))

    articles = []
    items = soup.select(selector) if selector else []
    for item in items[:max_items]:
        title_el = item.select_one(title_sel)
        content_el = item.select_one(content_sel)
        link_el = item.select_one(link_sel)
        url = urljoin(base_url, link_el.get("href", "")) if link_el else ""
        title = _clean_text(title_el.get_text(" ", strip=True) if title_el else "")
        content = _clean_text(content_el.get_text(" ", strip=True) if content_el else "")
        if not title:
            continue
        articles.append(
            {
                "title": title,
                "summary": content,
                "content": content,
                "url": url,
                "published": _extract_date(f"{title} {content}"),
            }
        )
    return articles


def _fetch_anchor_list(soup: BeautifulSoup, config: Dict) -> List[Dict]:
    selector = config.get("selector", "a")
    base_url = config.get("base_url", config.get("url", ""))
    include_href_keywords = config.get("include_href_keywords", []) or []
    include_text_keywords = config.get("include_text_keywords", []) or []
    exclude_href_keywords = config.get("exclude_href_keywords", []) or []
    exclude_title_keywords = config.get("exclude_title_keywords", []) or []
    min_text_length = int(config.get("min_text_length", 6))
    max_items = int(config.get("max_items", 30))

    seen = set()
    articles = []
    for anchor in soup.select(selector):
        href = anchor.get("href", "")
        title = _clean_text(anchor.get_text(" ", strip=True))
        if not href or not title or len(title) < min_text_length:
            continue

        full_url = urljoin(base_url, href)
        if include_href_keywords and not any(keyword in href or keyword in full_url for keyword in include_href_keywords):
            continue
        if include_text_keywords and not any(keyword in title for keyword in include_text_keywords):
            continue
        if any(keyword in href or keyword in full_url for keyword in exclude_href_keywords):
            continue
        if any(keyword in title for keyword in exclude_title_keywords):
            continue

        dedup_key = full_url or title
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        articles.append(
            {
                "title": title,
                "summary": title,
                "content": title,
                "url": full_url,
                "published": _extract_date(title),
            }
        )
        if len(articles) >= max_items:
            break

    return articles
