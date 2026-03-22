from typing import Dict, List


def fetch_rss(url: str, encoding: str = "utf-8", max_items: int = 30) -> List[Dict]:
    """从 RSS 源抓取文章。"""
    try:
        import feedparser
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少 feedparser 依赖，请先安装后再启用 RSS/RSSHub 资讯源") from exc

    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:max_items]:
        content_blocks = entry.get("content", []) or []
        content = ""
        if content_blocks:
            content = content_blocks[0].get("value", "")

        articles.append(
            {
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "content": content or entry.get("summary", ""),
                "url": entry.get("link", ""),
                "published": entry.get("published", "") or entry.get("updated", ""),
                "tags": [tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term")],
                "raw_payload": dict(entry),
            }
        )
    return articles
