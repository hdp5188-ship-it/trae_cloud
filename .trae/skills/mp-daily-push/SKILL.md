---
name: "mp-daily-push"
description: "Auto-generate WeChat public-account articles and push to draft box. Invoke when user says 'write a WeChat article about X' or 'schedule daily WeChat push'."
---

# mp-daily-push

公众号文章自动写作+推草稿 skill。整合「选题 → 搜热点 → LLM 写稿 → 图片上传 → draft/add」全链路。

## 两种模式

| 模式 | 触发 | 领域 | 调度 |
|---|---|---|---|
| **daemon** | `python3 scripts/daily_push.py daemon` | 每天自动一篇"临港" | 内置 `schedule` 库，常驻进程 |
| **manual** | `python3 scripts/daily_push.py manual --area <area>` | 手动指定（lingang / esports / sports / tech / ev） | 跑完一篇就退 |

## 目录结构

```
.trae/skills/mp-daily-push/
├── SKILL.md                  # 本文件
├── README.md                 # 使用说明 + 快速上手
├── config.example.json       # 配置模板（复制成 config.json 后填值）
└── scripts/
    └── daily_push.py         # 主脚本
```

## 快速上手（首次）

```bash
# 1. 复制配置模板
cp .trae/skills/mp-daily-push/config.example.json \
   /workspace/wechat-articles/mp-push.config.json

# 2. 编辑 config.json，填入：
#    WX_APPID / WX_APPSECRET
#    LLM_API_KEY（DeepSeek 或 Moonshot）
#    定时时间（默认每天 08:30，领域=临港）

# 3. 手动触发一篇测试（例如电竞）
python3 .trae/skills/mp-daily-push/scripts/daily_push.py \
  /workspace/wechat-articles/mp-push.config.json \
  manual --area esports

# 4. 后台常驻定时
nohup python3 .trae/skills/mp-daily-push/scripts/daily_push.py \
  /workspace/wechat-articles/mp-push.config.json daemon \
  >> /workspace/wechat-articles/logs/mp-push.log 2>&1 &
```

## 调用规则（Agent 端）

Agent 收到用户"写一篇 XX 领域的公众号"或"定时推送"请求时：

1. **手动触发**：拼命令 `python3 <skill-dir>/scripts/daily_push.py <config> manual --area <area>` 直接跑，把输出（media_id / 草稿链接路径）回给用户。
2. **定时调度**：确保 config.json 里 daemon.schedule 配好，用 nohup 或用户自己的 VPS 进程管理器起 daemon。
3. **领域关键词**：用户说"临港"→ lingang；"电竞"→ esports / gaming；"体育"→ sports；"科技/AI/芯片"→ tech；"电车/新能源车"→ ev。
4. **失败策略**：脚本内置 3 次重试 + 日志落盘到 `config.log_dir/YYYY-MM-DD.log`，Agent 只需最后 `tail` 日志确认状态。

## 依赖

- Python 3.8+
- `pip install requests schedule`
- 微信公众号：已认证服务号 + AppID/AppSecret + IP 白名单
- LLM API：推荐 DeepSeek（`deepseek-chat`）或 Moonshot（`moonshot-v1-8k`），token 自己申请

## 踩坑记录（实战验证，必读）

以下是真实发文过程中踩过的坑，每条都导致过用户明确返工。执行时逐条自检。

### 1. 图片必须"看过"，不能只看文件名/来源标签

- **反面案例**：一张命名为 `reuters-cr7-goal.jpg` 的图，实际是个穿黑 T 恤的老年男子，和 C 罗毫无关系，直接上了封面。
- 规则：每张图下载后**用图像识别读一遍**，确认①主体是不是文章写的人/物；②场景是否匹配正文段落；③脸是否清晰可辨。
- `og:image`、页面图库、图注都可能是文章页里的无关配图（作者头像、页脚 banner）。来源标注（"路透社/Stringer"）只说明出处，不保证内容对题。
- 图文必须一致：如果配图是"球场穿球衣"，正文就不能写"更衣室穿便服签字"。要么换图，要么改文字。

### 2. uploadimg 返回的 URL 必须原样使用，禁止截断

- 正确形态：`http://mmbiz.qpic.cn/sz_mmbiz_jpg/XXXX/0?from=appmsg`
- 少掉 `/0?from=appmsg` 或中间路径 → 打开 400，正文显示裂图。
- 写入 HTML 前做一次校验：`requests.get(url)` 必须返回 200 且 `content-type: image/*`。

### 3. draft 响应解码必须显式 UTF-8

- 微信响应头不带 charset，`requests` 会按 ISO-8859-1 猜，`r.json()` 出来是 `41å²æ´å¸½...` 这种假乱码。
- 取值一律用 `json.loads(r.content.decode('utf-8'))`。写入侧反过来：`json.dumps(data, ensure_ascii=False).encode('utf-8')` + `Content-Type: application/json; charset=utf-8`，否则中文变 `\uXXXX` 字面量，草稿箱里整篇乱码。

### 4. 三个隐藏字节上限

- `author` ≤ 12 字节（4 个汉字刚好卡满，5 个汉字直接报错）→ 超了就截断或先留空，发完让用户在后台补。
- `title` ≤ 64 字节、`digest` ≤ 120 字节。截断要落在完整 UTF-8 边界上，别把多字节字符劈一半。

### 5. GIF 动图是可行的，但要做格式/大小/帧数三重确认

- `media/uploadimg` 支持 gif，实测 3.6MB / 8MB / 9.4MB 均可上传，动画不会被压成静图。
- 封面（thumb）用 `material/add_material?type=thumb`，建议用静态 jpg，别用大 GIF。
- 上传后必须下载回来用 PIL 复核：`Image.open(f).n_frames` 帧数对不对、`size` 尺寸对不对。只看接口返回的 url 不算验证。
- WebP 需先转 JPEG（`PIL: im.convert('RGB').save('x.jpg', quality=95)`），uploadimg 不认 webp。

### 6. 找真实动图的可用路径

- 懂球帝文章被头条镜像后，`<img>` 的 `src` 是 `data:image/gif;base64` 占位符，真实地址在 `data-src` 属性里。
- 头条 CDN 的 `~tplv-tt-large.image` 后缀**不代表是静图**，实测返回 `image/gif` 且带完整帧动画。以下载后的 `file` / `content-type` 判断为准。
- 优先文字媒体（路透、Getty、新华社、澎湃、上海发布）；社媒转载图只做补充，且必须能认出主体。

### 7. 每次推完必须做终检

```
1) draft/get（强制 UTF-8 解码）→ 标题、摘要、正文中文正常，无 \uXXXX 字面量
2) 正文每张 <img> 的 src 逐个 GET → 全部 200 + image/*
3) 正文无残留本地路径（src="assets/..." 应已全部换成 CDN 地址）
4) draft/batchget 列出草稿 → 删掉同标题的旧重复稿，只留最新一条
```

第 4 步很重要：反复返工会堆出一串同标题草稿，用户打开会懵。

### 8. 交付前对用户说清"图是什么、从哪来"

每张图注明：位置（封面/中段）、画面内容（谁在做什么）、来源（媒体+摄影者）。用户会逐张核对，含糊其辞等于埋雷。
