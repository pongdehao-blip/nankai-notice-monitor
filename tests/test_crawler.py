from dataclasses import replace
from conftest import FakeFetcher,page,AT,body
from nankai_watch.state import empty_state
from nankai_watch.crawler import crawl
from nankai_watch.models import WatchError,FetchResult

def test_frontier_and_baseline(source):
    state=empty_state()
    p2=source.url.replace('list.htm','list2.htm')
    f=FakeFetcher({source.url:page(range(10,20),2),p2:page(range(1,10))})
    crawl(state,[source],f,at=AT)
    assert not state['events'] and len(state['notices'])==19
    f.calls.clear()
    crawl(state,[source],f,at=AT)
    assert len(f.calls)==1

def test_frontier_pinned_first_item_does_not_stop(source):
    state=empty_state()
    crawl(state,[source],FakeFetcher({source.url:page([1,2,3,4])}),at=AT)
    p2=source.url.replace('list.htm','list2.htm')
    f=FakeFetcher({source.url:page([1,20,21,22],2),p2:page([2,3,4])})
    crawl(state,[source],f,at=AT)
    assert len(f.calls)==2 and len(state['events'])==3

def test_overflow_stays_visible_until_original_frontier(source):
    state=empty_state()
    crawl(state,[source],FakeFetcher({source.url:page([1,2,3])}),at=AT)
    p2=source.url.replace('list.htm','list2.htm')
    p3=source.url.replace('list.htm','list3.htm')
    f=FakeFetcher({source.url:page([10,11,12],2),p2:page([7,8,9],3),p3:page([1,2,3])})
    crawl(state,[source],f,max_pages=2,at=AT)
    assert state['sources']['P01']['last_status']=='OVERFLOW_RISK'
    f.calls.clear()
    crawl(state,[source],f,max_pages=2,at=AT)
    assert len(f.calls)==2 and state['sources']['P01']['last_status']=='OVERFLOW_RISK'
    crawl(state,[source],f,max_pages=3,at=AT)
    assert state['sources']['P01']['last_status']=='OK'
    assert state['incidents']['P01:OVERFLOW_RISK']['recovered_at']==AT

def test_health_failure_then_recovery_and_partial_pages(source):
    state=empty_state()
    bad=FakeFetcher({source.url:WatchError('TIMEOUT','Timeout')})
    crawl(state,[source],bad,at=AT)
    assert not state['sources']['P01']['initialized']
    crawl(state,[source],FakeFetcher({source.url:page([1,2,3])}),at=AT)
    assert not state['events']
    assert state['incidents']['P01:TIMEOUT']['recovered_at']==AT

def test_empty_source_and_unexpected_empty(sources):
    s=next(s for s in sources if s.source_id=='J09')
    f=FakeFetcher({s.url:body('jwc-simple-empty-single.html')})
    state=empty_state()
    crawl(state,[s],f,at=AT)
    assert state['sources'][s.source_id]['last_status']=='OK'
    state['sources'][s.source_id]['ever_nonempty']=True
    crawl(state,[s],f,at=AT)
    assert state['sources'][s.source_id]['last_status']=='EMPTY_UNEXPECTED'

def test_conditional_304_reuses_parsed_cache(source):
    state=empty_state()
    crawl(state,[source],FakeFetcher({source.url:FetchResult(source.url,200,page([1,2,3]),'v1')}),at=AT)
    f=FakeFetcher({source.url:FetchResult(source.url,304)})
    crawl(state,[source],f,at=AT)
    assert not state['events'] and state['sources']['P01']['last_status']=='OK'
    assert f.calls[0][1]['etag']=='v1'
