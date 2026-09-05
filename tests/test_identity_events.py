from dataclasses import replace
from conftest import article,AT
from nankai_watch.identity import notice_id
from nankai_watch.normalize import normalize_url
from nankai_watch.state import empty_state
from nankai_watch.events import observe

def test_url_normalization():
    assert normalize_url('/_t12/2026/0905/c572a42/page.htm#x','https://PHYSICS.nankai.edu.cn')=='https://physics.nankai.edu.cn/2026/0905/c572a42/page.htm'
    assert normalize_url('https://jwc.nankai.edu.cn/_t12/a?meaningful=1#x').endswith('/_t12/a?meaningful=1')

def test_identity_and_no_false_merge(source):
    a=article(source)
    assert notice_id(a)==notice_id(replace(a,url=a.url.replace('c572','c999')))
    assert notice_id(a)!=notice_id(article(source,101))
    assert notice_id(replace(a,url='https://external.example/x?q=1'))!=notice_id(replace(a,url='https://external.example/x?q=2'))
    assert notice_id(replace(a,url=''))==notice_id(replace(a,url=''))

def test_baseline_events_and_dedup(source):
    state=empty_state()
    a=article(source)
    observe(state,[a],source,AT,baseline=True)
    assert not state['events']
    observe(state,[a],source,AT)
    assert not state['events']
    observe(state,[article(source,101)],source,AT)
    assert [e['type'] for e in state['events'].values()]==['NEW']
    other=replace(source,source_id='P02')
    observe(state,[replace(a,source_id='P02',url=a.url.replace('c572','c574'))],other,AT)
    assert len(state['notices'])==2
    assert state['notices'][notice_id(a)]['source_ids']==['P01','P02']

def test_update_title_and_date_no_removed(source):
    state=empty_state()
    a=article(source)
    observe(state,[a],source,AT,baseline=True)
    observe(state,[replace(a,title='修订通知')],source,AT)
    observe(state,[replace(a,title='修订通知',publish_date='2026-09-06')],source,AT)
    observe(state,[],source,AT)
    assert [e['type'] for e in state['events'].values()]==['UPDATED','UPDATED']

def test_different_source_stale_version_does_not_oscillate(source):
    state=empty_state()
    a=article(source)
    other=replace(source,source_id='P02')
    b=replace(a,source_id='P02',title='旧栏目标题')
    observe(state,[a],source,AT,baseline=True)
    observe(state,[b],other,AT,baseline=True)
    for _ in range(3):
        observe(state,[a],source,AT)
        observe(state,[b],other,AT)
    assert not state['events']
