from datetime import datetime,timedelta
import json
from unittest.mock import Mock
import pytest
import requests
from conftest import source,article,AT,page,FakeFetcher
from nankai_watch.state import empty_state,load_state
from nankai_watch.events import observe
from nankai_watch.service import daily
from nankai_watch.report.builder import build_report,split_report,encoded_size
from nankai_watch.report.feishu import FeishuClient
from nankai_watch.models import WatchError

def test_report_heartbeat_and_all_pending(source):
    state=empty_state()
    assert '心跳' in build_report(state,[source],AT).payloads[0]['content']['text']
    observe(state,[article(source)],source,'2026-08-01T00:00:00+00:00')
    report=build_report(state,[source],AT)
    assert len(report.event_ids)==1 and '测试通知' in report.payloads[0]['content']['text']

def test_report_split_no_truncation():
    original=('多字节汉字😀'+ '\\"\n')*9000
    chunks=split_report(original,'2026-09-05',1024)
    assert len(chunks)>1 and all(encoded_size(c)<=1024 for c in chunks)
    assert ''.join(c['content']['text'].split('\n',1)[1] for c in chunks)==original

@pytest.mark.parametrize('response_body,success',[
    ({'code':0},True),({'StatusCode':0},True),({'code':0,'StatusCode':0},True),
    ({'code':19001,'StatusCode':0},False),({},False),({'code':False},False),({'code':'0'},False)])
def test_feishu_delivery_acknowledgement(response_body,success):
    session=Mock()
    response=Mock(status_code=200)
    response.__enter__=Mock(return_value=response)
    response.__exit__=Mock(return_value=False)
    response.json.return_value=response_body
    session.post.return_value=response
    client=FeishuClient('https://open.feishu.cn/open-apis/bot/v2/hook/TEST_ONLY',session,sleep=lambda _:None)
    if success: client.send([{'msg_type':'text','content':{'text':'test'}}])
    else:
        with pytest.raises(WatchError): client.send([{}])

def test_webhook_never_in_error():
    session=Mock()
    session.post.side_effect=requests.ConnectionError('sensitive-url-value')
    client=FeishuClient('https://open.feishu.cn/open-apis/bot/v2/hook/TEST_ONLY',session)
    with pytest.raises(WatchError) as caught: client.send([{}])
    assert 'sensitive' not in str(caught.value)

def test_partial_delivery_keeps_pending_then_retry(source,tmp_path):
    state=empty_state()
    path=tmp_path/'state.json'
    f=FakeFetcher({source.url:page([1])})
    daily(state,[source],f,path,AT,dry_run=True)
    observe(state,[article(source,2)],source,AT)
    client=Mock()
    client.send.side_effect=WatchError('DELIVERY_ERROR','mock second chunk failure')
    with pytest.raises(WatchError): daily(state,[source],f,path,AT,client)
    state=load_state(path)
    assert all(e['reported_at'] is None for e in state['events'].values())
    client.send.side_effect=None
    def verify_pending_before_send(payloads):
        assert all(e['reported_at'] is None for e in load_state(path)['events'].values())
    client.send.side_effect=verify_pending_before_send
    daily(state,[source],f,path,AT,client)
    assert all(e['reported_at']==AT for e in load_state(path)['events'].values())
    assert daily(state,[source],f,path,AT,client)[2]=='no_changes'

def test_checkpoint_failure_prevents_delivery(source,tmp_path):
    state=empty_state()
    client=Mock()
    def fail(): raise WatchError('STATE_ERROR','push failed')
    with pytest.raises(WatchError):
        daily(state,[source],FakeFetcher({source.url:page([1])}),tmp_path/'state.json',AT,client,checkpoint=fail)
    client.send.assert_not_called()

def test_actual_second_chunk_failure_keeps_all_events(source,tmp_path):
    state=empty_state()
    path=tmp_path/'state.json'
    f=FakeFetcher({source.url:page([1])})
    daily(state,[source],f,path,AT,dry_run=True)
    for n in range(100,150):
        observe(state,[article(source,n,title='长通知标题'*100)],source,AT)
    session=Mock()
    good=Mock(status_code=200)
    good.__enter__=Mock(return_value=good)
    good.__exit__=Mock(return_value=False)
    good.json.return_value={'code':0}
    session.post.side_effect=[good,requests.Timeout()]
    client=FeishuClient('https://open.feishu.cn/open-apis/bot/v2/hook/TEST_ONLY',session,sleep=lambda _:None)
    with pytest.raises(WatchError): daily(state,[source],f,path,AT,client)
    assert session.post.call_count==2
    assert len(load_state(path)['events'])==50
    assert all(e['reported_at'] is None for e in load_state(path)['events'].values())

def test_report_site_order(sources):
    state=empty_state()
    selected=[next(s for s in sources if s.site_id==site) for site in ('nkzbb','jwc','physics')]
    for s in selected: observe(state,[article(s)],s,AT)
    text=build_report(state,sources,AT).payloads[0]['content']['text']
    assert text.index('物理科学学院')<text.index('教务部')<text.index('招投标管理办公室')<text.index('系统健康')
