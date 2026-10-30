#!/usr/bin/env python3
"""
mp-daily-push 主脚本：选题 → LLM 写稿 → 下载配图 → 推微信公众号草稿。

两种模式：
  daemon          常驻进程，每天定时自动生成临港领域文章
  manual          一次性运行，手动指定领域或具体话题

用法：
  python3 daily_push.py <config.json> daemon
  python3 daily_push.py <config.json> manual --area esports
  python3 daily_push.py <config.json> manual --topic "S16 瑞士轮 BLG vs TES"
"""
import argparse, json, logging, mimetypes, os, re, sys, time, uuid, urllib.request, urllib.parse
from datetime import datetime, date
from pathlib import Path

import requests
import schedule

# ---------- 日志 ----------
def setup_logging(log_dir: str):
    os.makedirs(log_dir, exist_ok=True)
    today = date.today().isoformat()
    log_file = os.path.join(log_dir, f"mp-push-{today}.log")
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt,
                        handlers=[logging.FileHandler(log_file, encoding='utf-8'),
                                  logging.StreamHandler(sys.stdout)])
    logging.info("log to %s", log_file)

# ---------- HTTP 工具 ----------
def _proxy_opener():
    """Build urllib opener honouring HTTP(S)_PROXY env vars."""
    proxies = {}
    for key in ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY'):
        val = os.environ.get(key)
        if val and key.lower().startswith('http'):
            proxies[key.split('_')[0]] = val
            proxies[key.split('_')[0] + 's'] = val
    if proxies:
        proxy_handler = urllib.request.ProxyHandler(proxies)
        return urllib.request.build_opener(proxy_handler)
    return None

_OPENER = _proxy_opener()

def http_get(url, timeout=30, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    opener = _OPENER or urllib.request.build_opener()
    with opener.open(req, timeout=timeout) as r:
        return r.read().decode('utf-8', errors='replace')

def http_post(url, data, timeout=60, headers=None):
    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    h = {'Content-Type': 'application/json; charset=utf-8'}
    if headers: h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))

def upload_file(url, file_path, field_name='media'):
    """Multipart file upload for WeChat media APIs."""
    boundary = '----TraeBoundary%s' % uuid.uuid4().hex
    ctype, _ = mimetypes.guess_type(file_path)
    if not ctype: ctype = 'application/octet-stream'
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        content = f.read()
    parts = []
    def add(s): parts.append(s.encode('utf-8'))
    add('--' + boundary)
    add(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"')
    add('Content-Type: ' + ctype)
    add('')
    parts.append(content)
    add('--' + boundary + '--')
    add('')
    body = b'\r\n'.join(parts)
    req = urllib.request.Request(url, data=body,
        headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode('utf-8')
    try:
        return json.loads(raw)
    except Exception:
        logging.error("raw upload response: %s", raw[:300])
        raise

# ---------- WeChat API ----------
def get_access_token(appid, appsecret):
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}'
    r = json.loads(http_get(url))
    if 'access_token' not in r:
        raise RuntimeError(f"token failed: {r}")
    logging.info("access_token OK, expires_in=%s", r['expires_in'])
    return r['access_token']

def upload_thumb(token, file_path):
    """Upload cover as thumb material. Response 'media_id' is what draft/add needs as thumb_media_id."""
    url = f'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb'
    r = upload_file(url, file_path)
    mid = r.get('thumb_media_id') or r.get('media_id')
    if not mid: raise RuntimeError(f"thumb upload failed: {r}")
    logging.info("thumb uploaded → media_id=%s", mid)
    return mid

def upload_news_image(token, file_path):
    """Upload an inline image for article body, returns CDN URL usable in <img>."""
    url = f'https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}'
    r = upload_file(url, file_path)
    wx_url = r.get('url')
    if not wx_url: raise RuntimeError(f"news_image upload failed: {r}")
    logging.info("news_image %s → %s", os.path.basename(file_path), wx_url[:70])
    return wx_url

def _truncate_for_wx(s: str, max_bytes: int = 12) -> str:
    """WeChat MP API hard limits — author = 12 bytes, title = 64 bytes, digest = 120 bytes."""
    if not s:
        return ''
    b = s.encode('utf-8')
    if len(b) <= max_bytes:
        return s
    # cut at last full multi-byte boundary
    while len(b) > max_bytes:
        b = b[:-1]
        if len(b) % 1 == 0:
            try:
                b.decode('utf-8')
                break
            except UnicodeDecodeError:
                continue
    return b.decode('utf-8')

def add_draft(token, thumb_media_id, title, author, digest, content_html):
    url = f'https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}'
    payload = {"articles": [{
        "title": _truncate_for_wx(title, 64),
        "author": _truncate_for_wx(author, 12),
        "digest": _truncate_for_wx(digest, 120),
        "content": content_html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }]}
    r = http_post(url, payload)
    logging.info("draft/add response: %s", json.dumps(r, ensure_ascii=False))
    if 'media_id' not in r:
        raise RuntimeError(f"draft/add failed: {r}")
    return r['media_id']

# ---------- 选题 ----------
def _fetch_feed_xml(url):
    """Fetch RSS/Atom feed XML. requests handles HTTP(S)_PROXY env natively."""
    r = requests.get(url, timeout=15, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; mp-daily-push/1.0)'
    })
    r.raise_for_status()
    return r.text

def _parse_feed_items(xml_text):
    """Very light XML regex parser for RSS <item> / Atom <entry> blocks. No external dep."""
    items = re.findall(r'<(?:item|entry)>(.*?)</\1>', xml_text, re.DOTALL | re.IGNORECASE) \
        if False else re.findall(r'<(?:item|entry)>(.*?)</(?:item|entry)>', xml_text, re.DOTALL | re.IGNORECASE)
    results = []
    for it in items:
        tag_t = re.search(r'<title[^>]*>(.*?)</title>', it, re.DOTALL | re.IGNORECASE)
        tag_l = re.search(r'<link[^>]*href?="?(.*?)"?[^>]*>', it, re.DOTALL | re.IGNORECASE)
        tag_d = re.search(r'<(?:description|summary)[^>]*>(.*?)</(?:description|summary)>',
                          it, re.DOTALL | re.IGNORECASE)
        if tag_t:
            title = re.sub(r'<[^>]+>', '', tag_t.group(1)).strip()
            link = (tag_l.group(1).strip() if tag_l else '')
            desc = re.sub(r'<[^>]+>', '', tag_d.group(1)).strip()[:200] if tag_d else ''
            if title:
                results.append({'title': title, 'link': link, 'summary': desc})
    return results

# A small roster of Chinese RSS feeds known to be accessible from most networks
_FALLBACK_FEEDS = [
    ('https://36kr.com/feed', '36kr'),
    ('https://www.pingwest.com/feed', 'pingwest'),
    ('https://feedx.net/rss/thepaper.xml', 'thepaper'),
]

def pick_topic_for_area(area_cfg, top_n=3):
    """Fetch news from configured news_sources → fallback to built-in roster.
    Return the most relevant item {title, link, summary}."""
    keywords = area_cfg.get('keywords', [])
    sources = list(area_cfg.get('news_sources') or []) + _FALLBACK_FEEDS
    for src in sources:
        url = src[0] if isinstance(src, tuple) else src
        try:
            xml = _fetch_feed_xml(url)
            items = _parse_feed_items(xml)
            if not items:
                continue
            # simple keyword scoring
            scored = []
            for it in items:
                blob = (it['title'] + ' ' + it.get('summary', '')).lower()
                score = sum(1 for k in keywords if k.lower() in blob)
                # bonus for shorter, catchier titles
                score += 1 if len(it['title']) < 40 else 0
                scored.append((score, it))
            scored.sort(key=lambda x: x[0], reverse=True)
            if scored:
                top = scored[0][1]
                logging.info("topic from %s: %s", url, top['title'][:50])
                return top
        except Exception as e:
            logging.debug("source %s failed: %s", url, e)
    # last-resort fallback
    generic_title = f"今天{area_cfg.get('name', '科技')}领域值得关注的一件事"
    return {'title': generic_title, 'link': '', 'summary': ''}

# ---------- LLM 写稿 ----------
def call_llm(llm_cfg, system_prompt, user_prompt):
    url = llm_cfg['base_url']
    api_key = llm_cfg['api_key']
    model = llm_cfg['model']
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    try:
        r = http_post(url, payload, timeout=llm_cfg.get('timeout', 60), headers=headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f"LLM HTTP {e.code}: {body[:300]}") from e
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e
    if 'choices' not in r:
        raise RuntimeError(f"LLM bad response: {json.dumps(r, ensure_ascii=False)[:400]}")
    content = r['choices'][0]['message']['content']
    # strip markdown code fences if present
    content = content.strip()
    if content.startswith('```'):
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
    logging.info("LLM returned %d chars", len(content))
    return content

def write_article(llm_cfg, prompt_tmpl, area_name, topic):
    system = prompt_tmpl['system'].replace('{AREA}', area_name)
    user = prompt_tmpl['user'].replace('{TOPIC}', topic['title'] + (" — " + topic['summary'][:120] if topic.get('summary') else ''))
    raw = call_llm(llm_cfg, system, user)
    # parse JSON
    try:
        data = json.loads(raw)
    except Exception:
        # try to extract JSON block
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
        else:
            raise
    required = ['title', 'body_html']
    for k in required:
        if k not in data:
            raise RuntimeError(f"LLM output missing key: {k}; raw tail={raw[-200:]}")
    logging.info("article title=%s, body_len=%d, images=%s",
                 data['title'], len(data['body_html']), len(data.get('images', [])))
    return data

# ---------- 图片下载 ----------
def download_images(image_list, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    local_mapping = {}  # remote_url -> local_rel_path (e.g. "assets/xxx.jpg")
    for i, img in enumerate(image_list or []):
        url = img.get('src', '') if isinstance(img, dict) else str(img)
        if not url or not url.startswith(('http://', 'https://')):
            continue
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or '.jpg'
        safe_name = f"img-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{i}{ext}"
        out_path = os.path.join(target_dir, safe_name)
        rel_path = f"assets/{safe_name}"
        try:
            with urllib.request.urlopen(url, timeout=20) as r, open(out_path, 'wb') as f:
                f.write(r.read())
            local_mapping[url] = rel_path
            logging.info("downloaded image → %s", rel_path)
        except Exception as e:
            logging.warning("image download failed %s: %s", url[:70], e)
    return local_mapping

def rewrite_body_local_to_wx(body_html, mapping):
    for local_rel, wx_url in mapping.items():
        body_html = body_html.replace(f'"{local_rel}"', f'"{wx_url}"')
    # also handle remaining "assets/xxx.jpg" not in mapping
    leftover = re.findall(r'src="(assets/[^"]+)"', body_html)
    if leftover:
        logging.warning("body still has local paths (will break in draft): %s", leftover)
    return body_html

# ---------- 一次完整推送 ----------
def run_once(config, area_key=None, manual_topic=None):
    """Generate + push one article. Returns draft media_id or raises."""
    article_root = config['article_root']
    # 1. 确定领域
    if manual_topic:
        area_key = area_key or 'tech'
        topic = {'title': manual_topic, 'link': '', 'summary': ''}
    else:
        area_key = area_key or config['daemon']['area']
        area_cfg = config['area_config'][area_key]
        logging.info("area=%s name=%s", area_key, area_cfg['name'])
        topic = pick_topic_for_area(area_cfg)

    area_name = config['area_config'].get(area_key, {}).get('name', area_key)
    logging.info("topic picked: %s", topic['title'])

    # 2. 写稿
    data = write_article(config['llm'], config['prompt_templates'], area_name, topic)

    # 3. 准备目录
    slug = datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + area_key
    work_dir = os.path.join(article_root, slug)
    assets_dir = os.path.join(work_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)

    # 4. 下载图片 → 本地
    local_mapping = download_images(data.get('images', []), assets_dir)

    # 5. 正文里的 remote URL 替换成本地路径
    body_local = data['body_html']
    for remote, local_rel in local_mapping.items():
        body_local = body_local.replace(f'"{remote}"', f'"{local_rel}"')

    # 6. 拿 token
    token = get_access_token(config['wechat']['appid'], config['wechat']['appsecret'])

    # 7. 上传封面（用第一张图）
    images_sorted = sorted(local_mapping.keys())  # deterministic order
    if images_sorted:
        cover_url = images_sorted[0]
        cover_local = local_mapping[cover_url]
        cover_abs = os.path.join(work_dir, cover_local)
        thumb_id = upload_thumb(token, cover_abs)
    else:
        thumb_id = ''
        logging.warning("no cover image — draft/add may fail")

    # 8. 上传所有正文图为 news_image，构建本地→wx CDN 映射
    wx_mapping = {}  # local_rel → wx_url
    for remote, local_rel in local_mapping.items():
        abs_path = os.path.join(work_dir, local_rel)
        wx_url = upload_news_image(token, abs_path)
        wx_mapping[local_rel] = wx_url

    # 9. 重写 body 为 CDN URL
    body_cdn = rewrite_body_local_to_wx(body_local, wx_mapping)

    # 10. 推草稿
    media_id = add_draft(
        token,
        thumb_media_id=thumb_id,
        title=data['title'],
        author=config['wechat'].get('author', ''),
        digest=data.get('summary', topic['title'])[:120],
        content_html=body_cdn
    )

    # 11. 落盘一份 body.html 便于后续手动调整
    with open(os.path.join(work_dir, 'body.html'), 'w', encoding='utf-8') as f:
        f.write(body_local)
    with open(os.path.join(work_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump({'title': data['title'], 'topic': topic, 'media_id': media_id,
                   'area': area_key, 'pushed_at': datetime.now().isoformat()},
                  f, ensure_ascii=False, indent=2)

    logging.info("✓ draft created: media_id=%s work_dir=%s", media_id, work_dir)
    return media_id

def run_once_with_retry(config, area_key=None, manual_topic=None, max_retry=3):
    last_err = None
    for attempt in range(1, max_retry + 1):
        try:
            return run_once(config, area_key, manual_topic)
        except Exception as e:
            last_err = e
            logging.error("attempt %d/%d failed: %s", attempt, max_retry, e)
            if attempt < max_retry:
                time.sleep(30)
    raise RuntimeError(f"all {max_retry} attempts failed: {last_err}")

# ---------- 调度 ----------
def run_daemon(config):
    schedule_time = config['daemon']['schedule']
    area = config['daemon']['area']
    logging.info("daemon mode: daily %s, area=%s", schedule_time, area)
    schedule.every().day.at(schedule_time).do(
        run_once_with_retry, config=config, area_key=area
    )
    # also run once immediately on start if no run today yet
    logging.info("daemon started; will next fire at %s", schedule_time)
    while True:
        schedule.run_pending()
        time.sleep(30)

# ---------- CLI ----------
AREAS = {'lingang', 'esports', 'sports', 'tech', 'ev'}

def main():
    p = argparse.ArgumentParser(description='mp-daily-push: WeChat MP auto-draft generator')
    p.add_argument('config', help='path to config.json')
    sub = p.add_subparsers(dest='mode', required=True)

    sub.add_parser('daemon', help='run as daily scheduler')

    m = sub.add_parser('manual', help='run once now')
    m.add_argument('--area', default=None, choices=sorted(AREAS),
                   help='area to generate; if omitted, must pass --topic')
    m.add_argument('--topic', default=None, help='exact topic to write (overrides area pick)')

    args = p.parse_args()
    cfg_path = args.config
    with open(cfg_path, encoding='utf-8') as f:
        config = json.load(f)
    setup_logging(config['log_dir'])

    if args.mode == 'daemon':
        run_daemon(config)
    elif args.mode == 'manual':
        if not args.area and not args.topic:
            print("ERROR: manual mode needs --area or --topic", file=sys.stderr)
            sys.exit(2)
        mid = run_once_with_retry(config, area_key=args.area, manual_topic=args.topic)
        print(f"✓ pushed draft media_id={mid}")

if __name__ == '__main__':
    main()
