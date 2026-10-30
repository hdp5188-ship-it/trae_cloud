#!/usr/bin/env python3
"""Push article as draft to WeChat Official Account."""
import json, os, re, sys, time, urllib.request, urllib.parse, mimetypes, uuid, ssl, io

APPID = os.environ.get('WX_APPID', 'wx838dc5b94781cc74')
APPSECRET = os.environ.get('WX_APPSECRET', '6cd4eac73b78a08af743e8f56f5856d5')
ASSETS_DIR = '/workspace/wechat-articles/article-2026-10-30-morning/assets'
BODY_HTML_PATH = '/workspace/wechat-articles/article-2026-10-30-morning/body.html'
TITLE = '今天，33位诺奖得主正在滴水湖边开会——世界顶尖科学家论坛开幕了'
SUMMARY = '今早坐16号线到滴水湖站，撞见33位诺奖图灵奖得主齐聚临港中心。还有邵峰——顶科奖创办以来第一位中国籍获奖者。阵容、奖项、论坛议题，以及普通人能凑的热闹，都在这儿。'

# ---------------- HTTP ----------------
def http_get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def http_post(url, data, headers=None):
    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def upload_file(url, file_path, field_name='media'):
    """Multipart file upload (for thumb/news_image media)."""
    boundary = '----TraeBoundary%s' % uuid.uuid4().hex
    ctype, _ = mimetypes.guess_type(file_path)
    if not ctype: ctype = 'application/octet-stream'
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        content = f.read()
    parts = []
    def add(s): parts.append(s.encode('utf-8'))
    add('--' + boundary)
    add('Content-Disposition: form-data; name="%s"; filename="%s"' % (field_name, filename))
    add('Content-Type: ' + ctype)
    add('')
    parts.append(content)
    add('--' + boundary + '--')
    add('')
    body = b'\r\n'.join(parts)
    req = urllib.request.Request(url, data=body,
        headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode('utf-8')
    try:
        return json.loads(raw)
    except Exception as e:
        print('RAW UPLOAD RESPONSE:', raw[:500], file=sys.stderr)
        raise

# ---------------- Step 1: token ----------------
def get_token():
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}'
    print('[1] fetching access_token ...')
    r = http_get(url)
    print('    token response keys:', sorted(r.keys()))
    if 'access_token' not in r:
        print('    FULL RESPONSE:', json.dumps(r, ensure_ascii=False))
        sys.exit(2)
    print('    expires_in =', r['expires_in'], 'seconds')
    return r['access_token']

# ---------------- Step 2: upload images ----------------
def upload_thumb(token, file_path):
    url = f'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb'
    print('[2] uploading cover as thumb:', os.path.basename(file_path))
    r = upload_file(url, file_path)
    print('    thumb response:', json.dumps(r, ensure_ascii=False))
    # thumb upload returns "media_id" (NOT "thumb_media_id") in response;
    # that value is what we pass as thumb_media_id to draft/add.
    mid = r.get('thumb_media_id') or r.get('media_id')
    if not mid:
        print('    FAILED — no media_id in response')
        sys.exit(3)
    return mid

def upload_news_image(token, file_path):
    """Upload an inline image via news_image endpoint — returns URL usable in article body."""
    url = f'https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}'
    print('[3] uploading inline image:', os.path.basename(file_path))
    r = upload_file(url, file_path)
    print('    news_image response:', json.dumps(r, ensure_ascii=False))
    if 'url' not in r:
        print('    FAILED to get url')
        sys.exit(4)
    return r['url']

# ---------------- Step 3: build body with real URLs ----------------
def rewrite_body_with_wx_urls(body_html, mapping):
    """Replace 'assets/xxx.jpg' with the WeChat CDN URL."""
    for local_path, wx_url in mapping.items():
        body_html = body_html.replace(f'"{local_path}"', f'"{wx_url}"')
    return body_html

# ---------------- Step 4: draft/add ----------------
def add_draft(token, thumb_media_id, title, author, digest, content_html):
    url = f'https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}'
    article = {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content_html,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }
    payload = {"articles": [article]}
    print('[4] calling draft/add ...')
    print('    article title:', title)
    print('    content length (chars):', len(content_html))
    r = http_post(url, payload)
    print('    draft/add response:', json.dumps(r, ensure_ascii=False))
    return r

# ---------------- main ----------------
def main():
    # 1. token
    token = get_token()
    print('    token OK (len=%d)' % len(token))
    print()

    # 2. list assets
    asset_files = sorted([f for f in os.listdir(ASSETS_DIR) if f.endswith(('.jpg','.png','.jpeg','.gif'))])
    print('[assets]', asset_files)

    # 2a. pick first as cover (thumb)
    cover_file = os.path.join(ASSETS_DIR, asset_files[0])
    thumb_media_id = upload_thumb(token, cover_file)
    print('    thumb_media_id =', thumb_media_id)
    print()

    # 3. upload ALL images as news_image (for body <img> tags)
    mapping = {}
    for fn in asset_files:
        local_rel = 'assets/' + fn
        wx_url = upload_news_image(token, os.path.join(ASSETS_DIR, fn))
        mapping[local_rel] = wx_url
        print('    OK:', local_rel, '->', wx_url[:80])
    print()

    # 4. read body and rewrite
    body_html = open(BODY_HTML_PATH, encoding='utf-8').read()
    body_rewritten = rewrite_body_with_wx_urls(body_html, mapping)

    # check no local paths left
    leftover = re.findall(r'src="(assets/[^"]+)"', body_rewritten)
    if leftover:
        print('    WARNING: leftover local paths in body:', leftover)
    else:
        print('    body rewrite OK — no local paths remaining')
    print()

    # 5. add draft
    r = add_draft(token, thumb_media_id, TITLE,
                  author='临港观察',
                  digest=SUMMARY,
                  content_html=body_rewritten)

    if 'media_id' in r:
        print('\n✓ DRAFT CREATED')
        print('  media_id =', r['media_id'])
        print('  you can view it in mp.weixin.qq.com → 图文素材 → 草稿箱')
    else:
        print('\n✗ DRAFT FAILED')
        sys.exit(10)

if __name__ == '__main__':
    main()
