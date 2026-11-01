#!/usr/bin/env python3
"""用无头浏览器解析抖音分享链接，下载无水印视频 / 图集。

原理：
  1. 分享短链 302 跳转后能拿到 aweme_id；
  2. 用移动端 UA 打开 www.douyin.com/video/{id}，会被重定向到 m.douyin.com 分享页；
  3. 该页面把作品数据直接塞进了 window._ROUTER_DATA（含 play_addr 的 uri），
     不需要 a_bogus 签名，也不需要登录；
  4. 把 playwm 接口换成 play，即可拿到无水印地址。

用法:
    python3 douyin_dl.py "<分享链接或分享口令>" [-o 输出目录]
"""

import json
import os
import re
import sys
import urllib.request

from playwright.sync_api import sync_playwright

UA_M = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
NO_WATERMARK = "https://aweme.snssdk.com/aweme/v1/play/?video_id={uri}&ratio=1080p&line=0"


def resolve_aweme_id(text: str) -> str:
    """从分享口令里抽出短链，跟随 302 拿到作品 id。"""
    m = re.search(r"https?://[^\s，,。]+", text)
    if not m:
        raise SystemExit("没在输入里找到链接")
    req = urllib.request.Request(m.group(0), headers={"User-Agent": UA_M})
    with urllib.request.urlopen(req, timeout=20) as r:
        final = r.geturl()
    hit = re.search(r"(?:video|note)/(\d+)", final) or re.search(r"modal_id=(\d+)", final)
    if not hit:
        raise SystemExit(f"跳转后没拿到作品 id: {final}")
    return hit.group(1)


def fetch_item(aweme_id: str, proxy: str | None) -> dict:
    """打开作品页，从 window._ROUTER_DATA 里取出作品数据。"""
    launch = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage",
                 "--disable-blink-features=AutomationControlled"],
    }
    if proxy:
        launch["proxy"] = {"server": proxy}

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
        for _ in range(25):  # 最多等 25 秒，等页面把数据写进 _ROUTER_DATA
            raw = page.evaluate(
                "() => window._ROUTER_DATA ? JSON.stringify(window._ROUTER_DATA) : ''")
            if raw and "item_list" in raw:
                break
            page.wait_for_timeout(1000)
        browser.close()

    if not raw or "item_list" not in raw:
        raise SystemExit("页面没拿到作品数据（可能被风控拦了），稍后重跑一次")

    data = json.loads(raw)
    for value in (data.get("loaderData") or {}).values():
        if isinstance(value, dict) and "videoInfoRes" in value:
            items = (value["videoInfoRes"] or {}).get("item_list") or []
            if items:
                return items[0]
    raise SystemExit("_ROUTER_DATA 里没有 item_list")


def pick_urls(item: dict) -> tuple[list[str], list[str]]:
    uri = (((item.get("video") or {}).get("play_addr") or {}).get("uri")) or ""
    video = [NO_WATERMARK.format(uri=uri)] if uri else []
    images = [u for img in (item.get("images") or []) for u in (img.get("url_list") or [])[:1]]
    return video, images


def safe(name: str, limit: int = 50) -> str:
    name = re.sub(r'[\\/:*?"<>|\n\r\t#]', " ", name).strip()
    return re.sub(r"\s+", " ", name)[:limit] or "douyin"


def download(url: str, path: str, referer: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA_M, "Referer": referer})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)
    print(f"已保存 {path}  ({os.path.getsize(path) / 1_048_576:.1f} MB)")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('用法: python3 douyin_dl.py "<分享链接>" [-o 目录]')
    raw = sys.argv[1]
    outdir = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else "."
    os.makedirs(outdir, exist_ok=True)

    aweme_id = resolve_aweme_id(raw)
    print(f"作品 id: {aweme_id}")

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    item = fetch_item(aweme_id, proxy)

    author = ((item.get("author") or {}).get("nickname") or "").strip()
    desc = (item.get("desc") or "").strip()
    cover = (((item.get("video") or {}).get("cover") or {}).get("url_list") or [""])[0]
    print(f"作者: {author}  时长: {(item.get('video') or {}).get('duration', 0) / 1000:.1f}s")
    print(f"文案: {desc[:50]}")

    base = safe(f"{author}_{desc}")
    referer = f"https://www.douyin.com/video/{aweme_id}"
    videos, images = pick_urls(item)

    if videos:
        download(videos[0], os.path.join(outdir, f"{base}.mp4"), referer)
        if cover:
            download(cover, os.path.join(outdir, f"{base}.jpg"), referer)
    elif images:
        for i, img in enumerate(images, 1):
            download(img, os.path.join(outdir, f"{base}_{i}.jpg"), referer)
    else:
        raise SystemExit("作品数据里没有可下载的地址")


if __name__ == "__main__":
    main()
