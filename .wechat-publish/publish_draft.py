#!/usr/bin/env python3
"""微信公众号自动建草稿：上传封面/正文图 → draft/add（只到草稿箱）。
凭据从同目录 .wx-credentials 读取（APPID=... 换行 SECRET=...）。
一次性保护：成功后写 .done-<DATE> 并删除 .armed；已有 .done-* 或缺 .armed 直接退出。
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CRED = os.path.join(HERE, ".wx-credentials")
LOG = os.path.join(HERE, "publish.log")
ROOT = "/workspace/wechat-articles"
BODY = os.path.join(ROOT, "dishui-lake-rail", "body.html")
ASSETS = os.path.join(ROOT, "assets")
DATE = time.strftime("%Y-%m-%d")
MARK = os.path.join(HERE, f".done-{DATE}")

TITLE = "热滑完成、首列车进厂，南汇支线离通车还差三步"
DIGEST = "国庆期间热滑试验完成，首列列车9月26日深夜运抵下盐路车辆基地，网友已拍到列车试跑；南汇支线转入联调联试阶段，明年7月通车目标又近一步。"
AUTHOR = "滴水湖"

BODY_IMG_MAP = [
    "assets/nanhui-line-testrun.jpg",
    "assets/nanhui-line-viaduct.jpg",
    "assets/nanhui-line-girder.jpg",
]
COVER = os.path.join(ASSETS, "nanhui-train-front.jpg")


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def api(path, params=None, payload=None, raw=None, ctype=None, method=None):
    url = "https://api.weixin.qq.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    if raw is not None:
        data, m, ct = raw, method or "POST", ctype
    elif payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        m, ct = method or "POST", "application/json; charset=utf-8"
    else:
        data, m, ct = None, method or "GET", None
    req = urllib.request.Request(url, data=data, method=m)
    if ct:
        req.add_header("Content-Type", ct)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def multipart(fields, files):
    boundary = "----wx" + str(int(time.time() * 1000))
    buf = []
    for k, v in fields.items():
        buf.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    for name, fname, path in files:
        buf.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{fname}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode())
        with open(path, "rb") as f:
            buf.append(f.read())
        buf.append(b"\r\n")
    buf.append(f"--{boundary}--\r\n".encode())
    return b"".join(buf), f"multipart/form-data; boundary={boundary}"


def main():
    if any(f.startswith(".done-") for f in os.listdir(HERE)):
        log("已成功执行过，退出")
        return 0
    if not os.path.exists(os.path.join(HERE, ".armed")):
        log("未上膛（无 .armed），退出")
        return 0
    if not os.path.exists(CRED):
        log("错误：凭据文件不存在 " + CRED)
        return 2
    cred = dict(l.strip().split("=", 1) for l in open(CRED, encoding="utf-8") if "=" in l)
    appid, secret = cred["APPID"].strip(), cred["SECRET"].strip()

    tok = api("/cgi-bin/token", {"grant_type": "client_credential", "appid": appid, "secret": secret})
    if "access_token" not in tok:
        log(f"取 token 失败: {tok}")
        return 3
    at = tok["access_token"]
    log("token 获取成功")

    # 1. 封面图（永久素材；临时素材在 draft/add 报 40007）
    body, ct = multipart({}, [("media", os.path.basename(COVER), COVER)])
    up = api("/cgi-bin/material/add_material", {"access_token": at, "type": "image"}, raw=body, ctype=ct)
    if "media_id" not in up:
        log(f"封面上传失败: {up}")
        return 4
    thumb = up["media_id"]
    log(f"封面上传成功 media_id={thumb[:20]}...")

    # 2. 正文图 → uploadimg 换 mmbiz 链接
    html = open(BODY, encoding="utf-8").read()
    for rel in BODY_IMG_MAP:
        path = os.path.join(ASSETS, os.path.basename(rel))
        body, ct = multipart({}, [("media", os.path.basename(path), path)])
        up = api("/cgi-bin/media/uploadimg", {"access_token": at}, raw=body, ctype=ct)
        if "url" not in up:
            log(f"正文图上传失败 {rel}: {up}")
            return 5
        html = html.replace(f'src="{rel}"', f'src="{up["url"]}"')
        log(f"正文图已替换: {rel}")

    # 3. 建草稿
    draft = api("/cgi-bin/draft/add", {"access_token": at}, payload={
        "articles": [{
            "title": TITLE,
            "author": AUTHOR,
            "digest": DIGEST,
            "content": html,
            "content_source_url": "",
            "thumb_media_id": thumb,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }],
    })
    if "media_id" not in draft:
        log(f"建草稿失败: {draft}")
        return 6
    with open(MARK, "w") as f:
        f.write(draft["media_id"])
    armed = os.path.join(HERE, ".armed")
    if os.path.exists(armed):
        os.remove(armed)
    log(f"草稿创建成功 media_id={draft['media_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
