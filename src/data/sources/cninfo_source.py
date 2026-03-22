from datetime import datetime, timedelta
from typing import Dict, List
from urllib.parse import urljoin

import requests


def fetch_cninfo_announcements(config: Dict) -> List[Dict]:
    """通过巨潮资讯公告接口获取公告列表。"""
    end_date = config.get("end_date") or datetime.now().strftime("%Y-%m-%d")
    start_date = config.get("start_date") or (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    response = requests.post(
        "http://www.cninfo.com.cn/new/hisAnnouncement/query",
        data={
            "pageNum": int(config.get("page_num", 1)),
            "pageSize": int(config.get("page_size", 30)),
            "column": config.get("column", "szse_latest"),
            "tabName": config.get("tab_name", "fulltext"),
            "plate": config.get("plate", ""),
            "stock": config.get("stock", ""),
            "searchkey": config.get("searchkey", ""),
            "secid": config.get("secid", ""),
            "category": config.get("category", ""),
            "trade": config.get("trade", ""),
            "seDate": f"{start_date}~{end_date}",
        },
        headers={
            "User-Agent": config.get("user_agent", "Mozilla/5.0"),
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
        },
        timeout=int(config.get("timeout", 15)),
    )
    response.raise_for_status()

    payload = response.json()
    articles: List[Dict] = []
    for item in payload.get("announcements", []) or []:
        announcement_time = item.get("announcementTime")
        published = ""
        if announcement_time:
            published = datetime.fromtimestamp(announcement_time / 1000).strftime("%Y-%m-%d %H:%M:%S")

        title = item.get("announcementTitle", "")
        sec_code = item.get("secCode", "")
        sec_name = item.get("secName", "")
        summary = f"{sec_name} {title}".strip()
        articles.append(
            {
                "title": title,
                "summary": summary,
                "content": summary,
                "url": urljoin("https://www.cninfo.com.cn/", item.get("adjunctUrl", "")),
                "published": published,
                "symbols": [sec_code] if sec_code else [],
                "tags": ["公告"],
                "raw_payload": item,
            }
        )
    return articles
