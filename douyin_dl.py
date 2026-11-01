#!/usr/bin/env python3
"""用无头浏览器解析抖音分享链接，拿到无水印视频地址并下载。

原理：抖音详情接口需要 a_bogus 签名，我们不去逆向它，
      而是让 Chromium 正常打开作品页，由页面自己的 JS 完成签名，
      我们只监听 /aweme/v1/web/aweme/detail/ 的响应体，取出 play_addr。

用法:
    python3 douyin_dl.py "https://v.douyin.com/xxxx/" [-o 目录]
"""

import json
import os
import re
import sys
import urllib.request

from playwright.sync_api import sync_playwright

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
DETAIL_API = "/aweme/v1/web/aweme/detail/"


def fetch_ttwid() -> str | None:
    """注册接口拿一个 ttwid，让浏览器看起来像正常回访用户。"""
    body = json.dumps({
        "region": "cn", "aid": 1768, "needFid": False,
        "service": "www.ixigua.com",
        "migrate_info": {"ticket": "", "source": "node"},
        "cbUrlProtocol": "https", "union": True,
    }).encode()
    req = urllib.request.Request(
        "https://ttwid.bytedance.com/ttwid/union/register/",
        data=body, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            m = re.search(r"ttwid=(.+?);", r.headers.get("Set-Cookie", ""))
            return m.group(1) if m else None
    except Exception:
        return None


def resolve_share_link(text: str) -> str:
    """从分享口令里抽出短链，跟随 302 拿到带 aweme_id 的作品地址。"""
    m = re.search(r"https?://[^\s，,]+", text)
    if not m:
        raise SystemExit("没找到链接")
    url = m.group(0)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        final = r.geturl()
    vid = re.search(r"(?:video|note)/(\d+)", final)
    if not vid:
        raise SystemExit(f"跳转后没拿到作品 id: {final}")
    return f"https://www.douyin.com/video/{vid.group(1)}"


def extract(detail: dict) -> dict:
    """从 aweme_detail 里取出下载信息。"""
    video = detail.get("video") or {}
    images = (detail.get("images") or [])
    urls = ((video.get("play_addr") or {}).get("url_list") or [])
    urls = [u.replace("playwm", "play") for u in urls]
    return {
        "aweme_id": detail.get("aweme_id"),
        "desc": (detail.get("desc") or "").strip(),
        "author": ((detail.get("author") or {}).get("nickname") or "").strip(),
        "video_urls": urls,
        "images": [u for img in images for u in (img.get("url_list") or [])[:1]],
        "duration": (video.get("duration") or 0) / 1000,
    }


def safe(name: str, limit: int = 60) -> str:
    name = re.sub(r'[\\/:*?"<>|\n\r\t#]', " ", name).strip()
    return re.sub(r"\s+", " ", name)[:limit] or "douyin"


def download(url: str, out: str, referer: str) -> None:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": referer,
    })
    with urllib.request.urlopen(req, timeout=30) as r, open(out, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)
    print(f"已保存 {out} ({os.path.getsize(out) / 1_048_576:.1f} MB)")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('用法: python3 douyin_dl.py "<分享链接>" [-o 目录]')
    raw = sys.argv[1]
    outdir = "."
    if "-o" in sys.argv:
        outdir = sys.argv[sys.argv.index("-o") + 1]
    os.makedirs(outdir, exist_ok=True)

    page_url = resolve_share_link(raw)
    print(f"作品页: {page_url}")

    detail = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ])
        ctx = browser.new_context(
            user_agent=UA, locale="zh-CN",
            viewport={"width": 1440, "height": 900},
        )
        ttwid = fetch_ttwid()
        if ttwid:
            ctx.add_cookies([{
                "name": "ttwid", "value": ttwid, "domain": ".douyin.com",
                "path": "/", "expires": -1,
            }])

        page = ctx.new_page()

        def on_response(resp):
            nonlocal detail
            if DETAIL_API in resp.url:
                try:
                    data = resp.json()
                except Exception:
                    return
                if data.get("aweme_detail"):
                    detail = data["aweme_detail"]

        page.on("response", on_response)
        page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)
        for _ in range(20):  # 最多等 20 秒
            if detail:
                break
            page.wait_for_timeout(1000)

        browser.close()

    if not detail:
        raise SystemExit("没抓到详情数据，可能被验证码拦了，重跑一次试试")

    info = extract(detail)
    print(f"作者: {info['author']}  时长: {info['duration']:.1f}s  文案: {info['desc'][:40]}")

    base = safe(f"{info['author']}_{info['desc']}")
    if info["video_urls"]:
        download(info["video_urls"][0], os.path.join(outdir, f"{base}.mp4"), page_url)
    elif info["images"]:
        for i, img in enumerate(info["images"], 1):
            path = os.path.join(outdir, f"{base}_{i}.jpg")
            req = urllib.request.Request(img, headers={"User-Agent": UA, "Referer": page_url})
            with urllib.request.urlopen(req, timeout=30) as r, open(path, "wb") as f:
                f.write(r.read())
            print(f"已保存 {path}")
    else:
        raise SystemExit("详情里没有可下载的地址")


if __name__ == "__main__":
    main()
