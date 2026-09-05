import json
from dataclasses import replace
import pytest
from conftest import ROOT,body
from nankai_watch.adapters import ADAPTERS
from nankai_watch.models import WatchError

@pytest.mark.parametrize('site',['physics','jwc','nkzbb'])
def test_all_audit_layouts(site,sources):
    manifest=json.loads((ROOT/'artifacts/fixture_manifest.json').read_text(encoding='utf-8'))
    for fixture in manifest.values():
        if fixture['site_id']!=site: continue
        source=next(s for s in sources if s.source_id==fixture['source_id'])
        result=ADAPTERS[site].parse((ROOT/fixture['path']).read_bytes(),source,fixture['url'])
        assert [(i.title,i.url,i.publish_date) for i in result.items]==[(' '.join(i['title'].split()),i['url'],i['publish_date']) for i in fixture['items']]

def test_parser_jwc(sources):
    s=next(s for s in sources if s.source_id=='J01')
    items=ADAPTERS['jwc'].parse(body('J01-page1.html'),s,s.url).items
    assert items[0].publish_date=='2026-08-17'
    assert items[1].publish_date=='2026-09-04'

def test_parser_physics(source):
    items=ADAPTERS['physics'].parse(body('physics-list.html'),source,source.url).items
    assert next(i for i in items if '601400' in i.url).publish_date=='2026-08-24'

def test_parser_nkzbb(sources):
    s=next(s for s in sources if s.source_id=='Z09')
    result=ADAPTERS['nkzbb'].parse(body('nkzbb-intent-list.html'),s,s.url)
    assert result.items[1].title.endswith('（2026年第115批）')
    assert result.next_url.endswith('?curPage=2')
    with pytest.raises(WatchError,match='wrong page'):
        ADAPTERS['nkzbb'].parse(body('nkzbb-intent-list.html'),s,s.url+'?curPage=2')

def test_broken_selector_is_not_empty(source):
    with pytest.raises(WatchError):
        ADAPTERS['physics'].parse(b'<html/>',source,source.url)
