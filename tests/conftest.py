import json
from pathlib import Path
from dataclasses import replace
import pytest
from nankai_watch.config import load_sources
from nankai_watch.models import FetchResult,ParsedItem,WatchError

ROOT=Path(__file__).resolve().parents[1]
AT='2026-09-05T09:42:00+00:00'

@pytest.fixture
def sources():
    return load_sources(ROOT/'config/sources.yaml')

@pytest.fixture
def source(sources):
    return sources[0]

def body(name):
    return (ROOT/'tests/fixtures/audit'/name).read_bytes()

class FakeFetcher:
    def __init__(self,mapping):
        self.mapping=mapping
        self.calls=[]
    def fetch(self,url,**kwargs):
        self.calls.append((url,kwargs))
        value=self.mapping[url]
        if isinstance(value,Exception):
            raise value
        if isinstance(value,FetchResult):
            return value
        return FetchResult(url,200,value)
    def close(self):
        pass

def article(source,number=100,title='测试通知',date='2026-09-05'):
    return ParsedItem(source.source_id,source.site_id,title,f'https://{source.site_id}.nankai.edu.cn/2026/0905/c572a{number}/page.htm',date)

def page(numbers,next_page=None,title_prefix='通知'):
    rows=''.join(f'<li class="news"><span class="news_title"><a href="/2026/0905/c572a{n}/page.htm">{title_prefix}{n}</a></span><span class="news_meta">2026-09-05</span></li>' for n in numbers)
    next_link=f'<a class="next" href="/572/list{next_page}.htm">下一页</a>' if next_page else ''
    return f'<html><div id="wp_news_w6"><ul>{rows}</ul></div>{next_link}</html>'.encode()
