# Cloud Blender Render Service

一个最小可用的云端 Blender 渲染环境：上传 `.blend`，服务端用 GPU 渲染 PNG 序列，再用 ffmpeg 合成 MP4。App 通过 HTTP 提交任务、轮询进度、下载成片。

## 文件

| 文件 | 作用 |
|---|---|
| `app.py` | FastAPI 服务：鉴权、串行任务队列、进度、视频下载 |
| `render.py` | Blender 内执行：设置 Cycles/GPU/分辨率/帧率/帧范围，渲染 PNG |
| `make_test_scene.py` | 生成测试场景（人偶 + 推镜 + 红色警报灯） |
| `setup.sh` | Ubuntu GPU 机器一键安装 Blender + 服务 |
| `start.sh` | 读取环境变量并启动 uvicorn |
| `Dockerfile` / `docker-compose.yml` | 容器化部署（RunPod / 自建 GPU 服务器） |
| `smoke_test.sh` | 端到端冒烟测试 |

## 方式 A：AutoDL / 通用 Ubuntu GPU 机器（推荐，最省事）

1. 租实例：Ubuntu 22.04 + CUDA 12 镜像，RTX 4090 24G 足够 1080p。
2. 上传本目录：

```bash
scp -r cloud-render root@<实例地址>:/root/cloud-render
```

3. 安装并启动：

```bash
cd /root/cloud-render
sudo RENDER_ROOT=/root/autodl-tmp/render bash setup.sh
# setup.sh 会打印生成的 RENDER_TOKEN，记下来
sudo env ENV_FILE=/etc/blender-render.env nohup /opt/blender-render/start.sh \
  >/root/autodl-tmp/render.log 2>&1 &
curl http://127.0.0.1:8000/health
```

4. AutoDL 控制台把端口（默认 8000）映射为「自定义服务」，得到公网 URL。

> AutoDL 关机后 GPU 不计费，但数据盘可能继续计费；实例无公网入站，必须用它的自定义服务/隧道。

## 方式 B：Docker / RunPod

```bash
cp .env.example .env
# 编辑 .env，把 RENDER_TOKEN 换成随机长串（openssl rand -hex 32）
mkdir -p data && sudo chown -R 1000:1000 data   # 容器内以 uid 1000 运行
docker compose up -d --build
curl http://127.0.0.1:8000/health
```

RunPod：本地 `docker build -t <你的仓库>/blender-render:4.2 .` 并 push，然后创建 Pod 时填该镜像、暴露 HTTP 端口 8000、挂载网络卷到 `/data`、设置环境变量 `RENDER_TOKEN`。

## 配置

| 变量 | 默认 | 说明 |
|---|---|---|
| `RENDER_TOKEN` | 空 | 必填，Bearer Token；为空时拒绝所有请求 |
| `RENDER_ROOT` | `/data` | 任务与成片存放目录 |
| `BLENDER_BIN` | `blender` | Blender 可执行文件 |
| `FFMPEG_BIN` | `ffmpeg` | ffmpeg |
| `RENDER_DEVICE` | `auto` | `auto` / `gpu` / `cpu`，auto 找不到 GPU 自动退回 CPU |
| `MAX_UPLOAD_MB` | `4096` | `.blend` 上传上限 |
| `MAX_RENDER_MINUTES` | `240` | 单任务超时 |

## API

```bash
# 提交
curl -X POST http://127.0.0.1:8000/jobs \
  -H "Authorization: Bearer $RENDER_TOKEN" \
  -F "file=@scene.blend" \
  -F fps=24 -F start=1 -F end=360 \
  -F width=1920 -F height=1080 -F samples=96

# 查询
curl -H "Authorization: Bearer $RENDER_TOKEN" http://127.0.0.1:8000/jobs/<job_id>

# 下载
curl -H "Authorization: Bearer $RENDER_TOKEN" \
  http://127.0.0.1:8000/jobs/<job_id>/video -o out.mp4

# 删除
curl -X DELETE -H "Authorization: Bearer $RENDER_TOKEN" \
  http://127.0.0.1:8000/jobs/<job_id>
```

状态：`queued → running(render) → running(encode) → done / failed`，`progress` 为 0–100。

## 测试

```bash
export RENDER_TOKEN=<setup.sh 打印的 token>
bash smoke_test.sh
```

先跑 24 帧 640×360，确认链路通了，再上 1080p/360 帧。

## 场景注意事项

- 上传前执行 **File → External Data → Pack Resources**，否则贴图/HDRI 不会跟着 `.blend` 走。
- 服务端用 `--disable-autoexec` 启动 Blender，场景里的自动 Python 不会执行。
- 渲染参数（分辨率、fps、帧范围、采样数）由 API 覆盖，避免场景自带设置不一致。
- 1080p 建议 `samples=96` 左右并开启降噪；复杂场景显存可能逼近 24G，必要时换 A100 40G/80G。

## 安全

- 必须设置 `RENDER_TOKEN`，不要暴露无鉴权的 8000 端口；最好只允许你的 App 服务器 IP 访问。
- 容器内以非 root 用户运行；公网部署建议前面加 Caddy/Nginx 做 HTTPS。
- `.blend` 可能包含恶意脚本，虽然已禁用自动执行，仍建议只渲染自己的文件。

## 下一步

App 侧还需要三个代理接口（避免把 Token 放到浏览器）：

- `POST /api/cloud/render` → 转发上传
- `GET /api/cloud/render/:id` → 转发状态
- `GET /api/cloud/render/:id/video` → 下载到本地 `renders/`

需要的话我可以接着把这三条和界面里的「云端 Blender」面板做出来。
