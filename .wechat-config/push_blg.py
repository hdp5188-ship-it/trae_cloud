import json
import re
import time
import requests

CRED = '/workspace/.wechat-config/credentials.json'
BASE = 'https://api.weixin.qq.com'
ARTICLE_DIR = '/workspace/blg-dk-s16'

cred = json.load(open(CRED))
appid, secret = cred['appid'], cred['appsecret']


def call(method, url, tries=30, **kwargs):
    kwargs.setdefault('timeout', 60)
    last = None
    for i in range(tries):
        r = requests.request(method, url, **kwargs)
        try:
            data = r.json()
        except Exception:
            print('non-json', r.status_code, r.text[:100])
            return None
        if data.get('errcode') == 40164:
            ip = re.search(r'invalid ip ([0-9.:a-f]+)', data.get('errmsg', ''))
            print(f'  retry {i+1}: blocked {ip.group(1) if ip else "?"}')
            last = data
            time.sleep(2)
            continue
        return data
    return last


tok = call('GET', f'{BASE}/cgi-bin/token', params={
    'grant_type': 'client_credential', 'appid': appid, 'secret': secret
})
if not tok or 'access_token' not in tok:
    raise SystemExit(f'token error: {tok}')
token = tok['access_token']
print('token ok')

body = open(f'{ARTICLE_DIR}/body.html', encoding='utf-8').read()


def upload(src, name, kind):
    with open(f'{ARTICLE_DIR}/{src}', 'rb') as f:
        data = call('POST', f'{BASE}/cgi-bin/material/add_material',
                    params={'access_token': token, 'type': kind},
                    files={'media': (name, f, 'image/jpeg')}, timeout=120)
    if not data or 'media_id' not in data:
        raise SystemExit(f'upload error {src}: {data}')
    print('uploaded', src, 'ok')
    return data


cover = upload('assets/blg-cover.jpg', 'blg-cover.jpg', 'thumb')

for src, name in [('assets/blg-score.jpg', 'blg-score.jpg'),
                  ('assets/blg-matchup.jpg', 'blg-matchup.jpg'),
                  ('assets/weibo1.jpg', 'blg-weibo.jpg')]:
    if src not in body:
        print('WARN not referenced:', src)
        continue
    info = upload(src, name, 'image')
    body = body.replace(src, info['url'])

payload = {'articles': [{
    'title': '披萨！BLG 3-0 DK，韩国解说当场破防',
    'author': '',
    'digest': '瑞士轮送走MSI冠军HLE，八强淘汰EWC冠军DK——BLG本届世界赛，先后送走今年两座国际赛冠军。8条小龙，一条没放。',
    'content': body,
    'content_source_url': '',
    'thumb_media_id': cover['media_id'],
    'show_cover_pic': 1,
    'need_open_comment': 1,
    'only_fans_can_comment': 0,
}]}

r = call('POST', f'{BASE}/cgi-bin/draft/add', params={'access_token': token},
         data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
         headers={'Content-Type': 'application/json'}, timeout=90)
print('draft result:', json.dumps(r, ensure_ascii=False))
