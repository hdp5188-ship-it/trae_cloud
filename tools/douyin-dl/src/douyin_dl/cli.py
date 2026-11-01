"""命令行入口：dyfetch。"""

import argparse
import json
import os
import sys

from . import __version__
from .browser import ensure_chromium
from .core import FetchError, download, fetch_item, pick_urls, resolve_aweme_id, safe_name


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="dyfetch", description="抖音无水印视频 / 图集下载")
    ap.add_argument("link", help="抖音分享链接或整段分享口令")
    ap.add_argument("-o", "--out", default=".", help="输出目录（默认当前目录）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON，便于其他程序调用")
    ap.add_argument("--no-cover", action="store_true", help="不下载封面")
    ap.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    outdir = os.path.abspath(args.out)
    os.makedirs(outdir, exist_ok=True)

    try:
        ensure_chromium()
        aweme_id = resolve_aweme_id(args.link)
        item = fetch_item(aweme_id)
    except FetchError as e:
        print(f"解析失败: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # 网络、浏览器启动等
        print(f"运行失败: {e}", file=sys.stderr)
        return 1

    author = ((item.get("author") or {}).get("nickname") or "").strip()
    desc = (item.get("desc") or "").strip()
    cover = (((item.get("video") or {}).get("cover") or {}).get("url_list") or [""])[0]
    videos, images = pick_urls(item)
    referer = f"https://www.douyin.com/video/{aweme_id}"
    base = safe_name(f"{author}_{desc}")

    saved: list[dict] = []
    if videos:
        path = os.path.join(outdir, f"{base}.mp4")
        size = download(videos[0], path, referer)
        saved.append({"type": "video", "path": path, "bytes": size})
        if cover and not args.no_cover:
            cpath = os.path.join(outdir, f"{base}.jpg")
            saved.append({"type": "cover", "path": cpath,
                          "bytes": download(cover, cpath, referer)})
    elif images:
        for i, img in enumerate(images, 1):
            path = os.path.join(outdir, f"{base}_{i}.jpg")
            saved.append({"type": "image", "path": path,
                          "bytes": download(img, path, referer)})
    else:
        print("作品数据里没有可下载的地址", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "aweme_id": aweme_id,
            "author": author,
            "desc": desc,
            "duration": (item.get("video") or {}).get("duration", 0) / 1000,
            "files": saved,
        }, ensure_ascii=False, indent=2))
    else:
        for f in saved:
            print(f"已保存 {f['path']}  ({f['bytes'] / 1_048_576:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
