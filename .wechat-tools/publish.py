#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号 API 直发：上传图片素材 -> 组装正文 -> 建草稿 -> 发布 / 删草稿

关键点：请求体必须用 ensure_ascii=False 直发 UTF-8 汉字。
Python 的 json.dumps 默认 ensure_ascii=True 会把汉字转成 \\uXXXX，
微信服务端不还原这层转义，存库后前台就会显示成字面 \u5c71 乱码。
"""
import argparse
import io
import json
import os
import re
import sys

import requests
from PIL import Image

BASE = "https://api.weixin.qq.com"
APPID = os.environ.get("WX_APPID", "")
SECRET = os.environ.get("WX_SECRET", "")
IMG_WIDTH = 1080
JPEG_QUALITY = 82
MAX_RETRY = 12

TITLE_BYTES = 64      # title 按 UTF-8 字节限
DIGEST_BYTES = 120    # digest 实测：96 字节过、180 字节拒，取 120 保守值


def die(msg, code=None):
    print(f"[失败] {msg}" + (f" (errcode={code})" if code else ""), file=sys.stderr)
    sys.exit(1)


def note(errcode, errmsg):
    if errcode == 40164:
        return "IP 不在白名单，把错误里的地址补进后台「基本配置 → IP白名单」。"
    if errcode == 40001:
        return "access_token 无效或过期，重新执行 token。"
    if errcode == 45003:
        return f"title 超长：{TITLE_BYTES} 字节上限（中文约 {TITLE_BYTES // 3} 字）。"
    if errcode == 45004:
        return f"digest 超长：{DIGEST_BYTES} 字节上限（中文约 {DIGEST_BYTES // 3} 字）。"
    if errcode == 45110:
        return "author 字段异常，用空值即可。"
    if errcode == 45064:
        return "thumb_media_id 无效，先执行 upload。"
    if errcode == 53401:
        return "封面图片尺寸不合法或素材尚未就绪，稍等重试。"
    if errcode == 48001:
        return "接口权限不足：该类型公众号不支持此接口（订阅号无法发布，只能建草稿）。"
    if errcode == 40013:
        return "AppID 不正确。"
    if errcode == 40125:
        return "AppSecret 不正确。"
    return errmsg


def call(method, path, *, token=None, payload=None, files=None, params=None):
    """调用微信接口。请求体用 ensure_ascii=False 直发 UTF-8（见文件头说明）。"""
    url = f"{BASE}{path}"
    q = dict(params or {})
    if token:
        q["access_token"] = token

    kwargs = {"timeout": 60}
    if payload is not None:
        kwargs["data"] = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        kwargs["headers"] = {"Content-Type": "application/json; charset=utf-8"}
    if files:
        kwargs["files"] = {k: (v[0], bytes(v[1]), v[2]) for k, v in files.items()}

    last = None
    for attempt in range(MAX_RETRY):
        try:
            r = requests.request(method, url, params=q, **kwargs)
            data = r.json()
        except Exception as e:
            last = f"请求异常: {e}"
            continue
        errcode = data.get("errcode", 0)
        if errcode == 0:
            if attempt:
                print(f"      [重试] 第 {attempt + 1} 次请求通过")
            return data
        if errcode == 40164:
            m = re.search(r"invalid ip ([0-9.]+)", data.get("errmsg", ""))
            print(f"      [重试] 出口 {m.group(1) if m else '?'} 未在白名单 "
                  f"({attempt + 1}/{MAX_RETRY})", file=sys.stderr)
            last = data.get("errmsg")
            continue
        die(f"{path}: {note(errcode, data.get('errmsg'))}", errcode)
    die(f"{path}: 连续 {MAX_RETRY} 次被拒（{last}）", 40164)


def get_token():
    if not APPID or not SECRET:
        die("缺少环境变量 WX_APPID / WX_SECRET")
    data = call("GET", "/cgi-bin/token", params={
        "grant_type": "client_credential", "appid": APPID, "secret": SECRET,
    })
    tok = data.get("access_token")
    if not tok:
        die(f"未拿到 access_token: {data}")
    print(f"[OK] access_token 有效 {data.get('expires_in')} 秒")
    return tok


def check_sizes(title, digest):
    t, d = len(title.encode()), len(digest.encode())
    if t > TITLE_BYTES:
        die(f"标题 {t} 字节超限（上限 {TITLE_BYTES}，约 {TITLE_BYTES // 3} 个中文）")
    if d > DIGEST_BYTES:
        die(f"摘要 {d} 字节超限（上限 {DIGEST_BYTES}，约 {DIGEST_BYTES // 3} 个中文）")
    print(f"[OK] 标题 {t}/{TITLE_BYTES} 字节 · 摘要 {d}/{DIGEST_BYTES} 字节")


def shrink(data):
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if img.width > IMG_WIDTH:
        h = round(img.height * IMG_WIDTH / img.width)
        img = img.resize((IMG_WIDTH, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)
    out = buf.getvalue()
    print(f"      {len(data)//1024} KB -> {len(out)//1024} KB ({img.width}x{img.height})")
    return out


def upload_image(token, path):
    shrunk = shrink(open(path, "rb").read())
    files = {"media": (os.path.basename(path), shrunk, "image/jpeg")}
    data = call("POST", "/cgi-bin/material/add_material", token=token,
                params={"type": "image"}, files=files)
    if not data.get("url") or not data.get("media_id"):
        die(f"上传未返回 url/media_id: {data}")
    print(f"      -> {data['url'][:70]}...")
    return {"path": path, "url": data["url"], "media_id": data["media_id"]}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("token")

    p = sub.add_parser("upload")
    p.add_argument("images", nargs="+")
    p.add_argument("--out", required=True)

    p = sub.add_parser("draft")
    p.add_argument("--body", required=True)
    p.add_argument("--map", dest="mapfile", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--digest", default="")
    p.add_argument("--author", default="")
    p.add_argument("--cover", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("publish")
    p.add_argument("--media-id", required=True)

    p = sub.add_parser("delete")
    p.add_argument("media_id")

    args = ap.parse_args()

    if args.cmd == "token":
        get_token()

    elif args.cmd == "upload":
        tok = get_token()
        res = [upload_image(tok, p) for p in args.images]
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"[OK] 素材映射 -> {args.out}")

    elif args.cmd == "draft":
        check_sizes(args.title, args.digest)
        tok = get_token()
        mapping = json.load(open(args.mapfile, encoding="utf-8"))
        content = open(args.body, encoding="utf-8").read()
        by_name = {os.path.basename(m["path"]): m for m in mapping}

        missing = set(re.findall(r'assets/([^"\')\s]+)', content)) - set(by_name)
        if missing:
            die(f"正文引用了未上传的图片: {sorted(missing)}")
        for name, m in sorted(by_name.items(), key=lambda x: -len(x[0])):
            content = content.replace(f"assets/{name}", m["url"])
        left = re.findall(r'assets/[^"\')\s]+', content)
        if left:
            die(f"仍有本地图片路径未替换: {left}")

        cover = by_name[os.path.basename(args.cover)]
        payload = {"articles": [{
            "title": args.title,
            "author": args.author,
            "digest": args.digest,
            "content": content,
            "content_source_url": "",
            "thumb_media_id": cover["media_id"],
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]}
        data = call("POST", "/cgi-bin/draft/add", token=tok, payload=payload)
        mid = data.get("media_id")
        if not mid:
            die(f"建草稿失败: {data}")
        open(args.out, "w", encoding="utf-8").write(mid)
        print(f"[OK] 草稿 media_id = {mid}")
        print("     后台「内容管理 → 草稿箱」可预览")

    elif args.cmd == "publish":
        tok = get_token()
        data = call("POST", "/cgi-bin/freepublish/submit", token=tok,
                    payload={"media_id": args.media_id})
        pid = data.get("publish_id")
        print(f"[OK] 已提交发布 publish_id = {pid}")
        for _ in range(10):
            st = call("POST", "/cgi-bin/freepublish/get", token=tok,
                      payload={"publish_id": pid})
            s = st.get("publish_status")
            if s == 3:
                print("[OK] 发布成功")
                return
            if s == 4:
                die(f"发布失败: {st}")
            print(f"     处理中 (status={s})...")
        print("[!] 查询超时，稍后到后台确认")

    elif args.cmd == "delete":
        tok = get_token()
        call("POST", "/cgi-bin/draft/delete", token=tok,
             payload={"media_id": args.media_id})
        print(f"[OK] 已删除草稿 {args.media_id[:24]}...")


if __name__ == "__main__":
    main()
