"""解析与下载核心逻辑。"""

import json
import os
import re
import urllib.request

from playwright.sync_api import sync_playwright

from .browser import browser_proxy

UA_M = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
NO_WATERMARK = "https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"


class FetchError(RuntimeError):
    """解析失败：被风控、作品不存在、页面结构变化等。"""


def resolve_aweme_id(text: str) -> str:
    """从分享口令里抽出链接，跟随 302 拿到作品 id。"""
    m = re.search(r"https?://[^\s，,。]+", text)
    if not m:
        raise FetchError("没在输入里找到链接")
    req = urllib.request.Request(m.group(0), headers={"User-Agent": UA_M})
    with urllib.request.urlopen(req, timeout=20) as r:
        final = r.geturl()
    hit = re.search(r"(?:video|note)/(\d+)", final) or re.search(r"modal_id=(\d+)", final)
    if not hit:
        raise FetchError(f"跳转后没拿到作品 id: {final}")
    return hit.group(1)


def fetch_item(aweme_id: str, retries: int = 2) -> dict:
    """打开移动端分享页，从 window._ROUTER_DATA 取作品数据。"""
    launch = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage",
                 "--disable-blink-features=AutomationControlled"],
    }
    proxy = browser_proxy()
    if proxy:
        launch["proxy"] = proxy

    last = ""
    for _ in range(retries):
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch)
            ctx = browser.new_context(
                user_agent=UA_M, locale="zh-CN", is_mobile=True,
                viewport={"width": 390, "height": 844},
            )
            page = ctx.new_page()
            page.goto(f"https://www.douyin.com/video/{aweme_id}",
                      wait_until="domcontentloaded", timeout=45_000)

            raw = ""
            for _ in range(25):  # 最多等 25 秒，等页面写入 _ROUTER_DATA
                raw = page.evaluate(
                    "() => window._ROUTER_DATA ? JSON.stringify(window._ROUTER_DATA) : ''")
                if raw and "item_list" in raw:
                    break
                page.wait_for_timeout(1000)
            browser.close()

        last = raw
        if raw and "item_list" in raw:
            data = json.loads(raw)
            for value in (data.get("loaderData") or {}).values():
                if isinstance(value, dict) and "videoInfoRes" in value:
                    items = (value["videoInfoRes"] or {}).get("item_list") or []
                    if items:
                        return items[0]
    raise FetchError("页面没拿到作品数据，可能被风控拦了" if not last else "分享页结构变了")


def pick_urls(item: dict) -> tuple[list[str], list[str]]:
    """play_addr 的 uri 转成无水印地址；图集则取图片列表。"""
    uri = (((item.get("video") or {}).get("play_addr") or {}).get("uri")) or ""
    video = [NO_WATERMARK.format(uri=uri)] if uri else []
    images = [u for img in (item.get("images") or []) for u in (img.get("url_list") or [])[:1]]
    return video, images


def safe_name(name: str, limit: int = 50) -> str:
    name = re.sub(r'[\\/:*?"<>|\n\r\t#]', " ", name).strip()
    return re.sub(r"\s+", " ", name)[:limit] or "douyin"


def download(url: str, path: str, referer: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA_M, "Referer": referer})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)
    return os.path.getsize(path)
