# douyin-dl

抖音无水印视频 / 图集下载工具，命令行使用，可在任意目录、任意项目里调用。

## 安装（任何一台电脑）

```bash
pipx install "git+https://github.com/hdp5188-ship-it/trae_cloud.git@main#subdirectory=tools/douyin-dl"
```

装完就有全局命令 `dyfetch`。首次运行会自动下载 Chromium（约 110MB）；若系统缺库，再执行一次：

```bash
python3 -m playwright install-deps chromium
```

本地改动时用可编辑安装：

```bash
pipx install -e ./tools/douyin-dl --force
```

## 用法

```bash
dyfetch "9.97 复制打开抖音... https://v.douyin.com/xxxx/"      # 下载到当前目录
dyfetch "https://v.douyin.com/xxxx/" -o ~/Videos               # 指定目录
dyfetch "https://v.douyin.com/xxxx/" --json                    # 输出 JSON 给其他程序用
dyfetch --help
```

图集作品会自动逐张保存为 jpg。

## 工作原理

1. 分享短链 302 跳转，拿到 `aweme_id`；
2. 用移动端 UA 打开 `www.douyin.com/video/{id}`，重定向到 `m.douyin.com` 分享页；
3. 该页把作品数据写在 `window._ROUTER_DATA` 里，无需 `a_bogus` 签名、无需登录；
4. 取 `video.play_addr.uri`，把 `playwm` 接口换成 `play`，即得无水印地址。

桌面站（不带移动 UA）会触发登录 + 滑块验证，所以这里固定走移动端分享页。

## 限制

- 依赖 `m.douyin.com` 分享页结构，抖音改版后可能需要更新解析逻辑；
- `ratio=1080p` 只是请求参数，实际分辨率以源视频为准；
- 仅用于个人学习与备份，请勿用于二次分发或商业用途。
