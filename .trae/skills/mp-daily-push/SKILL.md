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
