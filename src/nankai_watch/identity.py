import hashlib
import re
from urllib.parse import urlsplit
from .normalize import normalize_url, normalize_title

ARTICLE_ID=re.compile(r'/c\d+a(\d+)/page\.htm$')


def notice_id(item):
    if item.url:
        url=normalize_url(item.url)
        u=urlsplit(url)
        match=ARTICLE_ID.search(u.path)
        if item.site_id in ('physics','jwc') and u.hostname==item.site_id+'.nankai.edu.cn' and match:
            return f'{item.site_id}:article:{match.group(1)}'
        key=url
    else:
        key=normalize_title(item.title)+'|'+(item.publish_date or '')
    return item.site_id+':url:'+hashlib.sha256(key.encode()).hexdigest()
