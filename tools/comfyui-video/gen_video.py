#!/usr/bin/env python3
"""AutoDL.Art ComfyUI 工作流调用：提交任务、轮询、下载产出。

用法示例:
  python tools/comfyui-video/gen_video.py --prompt "海边日落，无人机俯拍，电影感"
  python tools/comfyui-video/gen_video.py --workflow minimax_h3_z0901 \
      --prompt "..." --duration 5 --resolution "768p竖(768*1344)"

配置读取同目录 .env:
  COMFYUI_API_BASE=https://autodl.art
  COMFYUI_TOKEN=<在 autodl.art 创建的 ComfyUI 分组令牌>
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.abspath(os.path.join(HERE, "..", "..", "out"))


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def api(base, token, path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Authorization": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        raise SystemExit(f"HTTP {e.code}: {raw}")


def build_body(rules, overrides):
    body = {}
    for name, rule in rules.items():
        default = rule.get("default")
        if isinstance(default, str) and default.startswith("default_local_path"):
            default = ""
        if default is not None:
            body[name] = default
    body.update(overrides)
    for name, rule in rules.items():
        if rule.get("required") and body.get(name) in (None, ""):
            raise SystemExit(f"缺少必填参数: {name}")
    return body


def parse_value(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def download(url, dest):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def main():
    load_env(os.path.join(HERE, ".env"))
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", default="minimax_h3_z0901", help="工作流 uuid")
    p.add_argument("--prompt", required=True)
    p.add_argument("--duration", type=int)
    p.add_argument("--resolution")
    p.add_argument("--seed", type=int)
    p.add_argument("--param", action="append", default=[], metavar="KEY=VALUE",
                   help="额外参数，可重复，值会按 JSON 解析")
    p.add_argument("--out", default=DEFAULT_OUT)
    p.add_argument("--interval", type=int, default=10, help="轮询间隔秒")
    p.add_argument("--timeout", type=int, default=1800, help="最长等待秒")
    a = p.parse_args()

    base = os.environ.get("COMFYUI_API_BASE", "https://autodl.art").rstrip("/")
    token = os.environ.get("COMFYUI_TOKEN", "").strip()
    if not token:
        raise SystemExit("未配置 COMFYUI_TOKEN，请先填入 tools/comfyui-video/.env")

    detail = api(base, token, f"/api/v1/comfyui/workflows/{a.workflow}")
    if detail.get("code") != "Success":
        raise SystemExit(f"读取工作流失败: {detail}")
    rules = detail["data"].get("input_rules", {})

    overrides = {"prompt": a.prompt}
    for key, val in (("duration", a.duration), ("resolution", a.resolution), ("seed", a.seed)):
        if val is not None:
            overrides[key] = val
    for item in a.param:
        k, v = item.split("=", 1)
        overrides[k] = parse_value(v)

    body = build_body(rules, overrides)
    print("提交参数:", json.dumps(body, ensure_ascii=False))

    sub = api(base, token, f"/api/v1/comfyui/comfyui_workflow/{a.workflow}", "POST", body)
    if sub.get("code") != "Success":
        raise SystemExit(f"提交失败: {sub}")
    task_id = sub["data"]["task_id"]
    print("task_id:", task_id)

    deadline = time.time() + a.timeout
    data = {}
    while time.time() < deadline:
        data = api(base, token, f"/api/v1/comfyui/comfyui_workflow/result/{task_id}")
        if data.get("code") != "Success":
            raise SystemExit(f"查询失败: {data}")
        data = data["data"]
        status = data.get("status")
        print(f"[{time.strftime('%H:%M:%S')}] status={status}")
        if status not in ("QUEUED", "RUNNING"):
            break
        time.sleep(a.interval)
    else:
        raise SystemExit(f"超时，task_id={task_id}（任务可能仍在服务端运行）")

    if status == "SUCCESS":
        os.makedirs(a.out, exist_ok=True)
        results = data.get("results") or []
        if not results:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            raise SystemExit("任务成功但没有返回产出")
        for i, r in enumerate(results):
            url = r.get("url", "")
            ext = os.path.splitext(url.split("?")[0])[1] or ""
            dest = os.path.join(a.out, f"{task_id}_{i}{ext}")
            print(f"下载 {r.get('type')} -> {dest}")
            download(url, dest)
        meta = os.path.join(a.out, f"{task_id}.json")
        with open(meta, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("完成:", meta)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        raise SystemExit(f"任务结束状态: {status}")


if __name__ == "__main__":
    main()
