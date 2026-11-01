"""浏览器准备：首次使用自动装 Chromium。"""

import os
import subprocess
import sys

MIRROR = "https://cdn.npmmirror.com/binaries/playwright"


def ensure_chromium() -> None:
    """Chromium 不存在时自动下载一次（约 110MB）。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        path = p.chromium.executable_path
    if os.path.exists(path):
        return

    print("首次运行，正在下载 Chromium ...", file=sys.stderr)
    env = {**os.environ}
    if not any(k in os.environ for k in ("HTTPS_PROXY", "https_proxy")):
        env["PLAYWRIGHT_DOWNLOAD_HOST"] = MIRROR
    else:
        env.setdefault("PLAYWRIGHT_DOWNLOAD_HOST", MIRROR)
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env, check=True,
    )


def browser_proxy() -> dict | None:
    """Playwright 不继承 http_proxy，需要显式传入。"""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    return {"server": proxy} if proxy else None
