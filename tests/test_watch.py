from unittest.mock import Mock
import pytest
from conftest import AT,FakeFetcher,page,article
from nankai_watch.service import watch
from nankai_watch.state import empty_state,load_state
from nankai_watch.events import observe
from nankai_watch.models import WatchError


def test_silent_baseline_and_unchanged_preserve_old_daily_state(source,tmp_path):
    state=empty_state()
    state['delivery']={'last_success_date':'2026-09-05','last_success_at':AT}
    client=Mock()
    f=FakeFetcher({source.url:page([1])})
    for _ in range(2):
        assert watch(state,[source],f,tmp_path/'s.json',AT,client)[2]=='no_changes'
    client.send.assert_not_called()
    assert not state['events']
    assert state['delivery']['last_success_at']==AT


def test_two_batches_same_day_and_update_at_night(source,tmp_path):
    state=empty_state()
    path=tmp_path/'s.json'
    client=Mock()
    watch(state,[source],FakeFetcher({source.url:page([1])}),path,AT,client)
    state['delivery']['last_success_date']='2026-09-05'
    for ids in ([2,1],[3,2,1]):
        assert watch(state,[source],FakeFetcher({source.url:page(ids)}),path,AT,client)[2]=='sent'
    assert client.send.call_count==2
    night='2026-09-06T02:42:00+08:00'
    f=FakeFetcher({source.url:page([3,2,1],title_prefix='已修订通知')})
    assert watch(state,[source],f,path,night,client)[2]=='sent'
    text=client.send.call_args.args[0][0]['content']['text']
    assert 'UPDATED 更新' in text and '02:42:00' in text
    assert watch(state,[source],f,path,night,client)[2]=='no_changes'
    assert client.send.call_count==3


def test_date_only_update_sends(source,tmp_path):
    state=empty_state()
    path=tmp_path/'s.json'
    client=Mock()
    f=FakeFetcher({source.url:page([1])})
    watch(state,[source],f,path,AT,client)
    changed=page([1]).replace(b'2026-09-05',b'2026-09-06')
    assert watch(state,[source],FakeFetcher({source.url:changed}),path,AT,client)[2]=='sent'
    assert 'UPDATED 更新' in client.send.call_args.args[0][0]['content']['text']


def test_failure_only_alert_repeats_per_round_and_recovery_is_silent(source,tmp_path):
    state=empty_state()
    client=Mock()
    path=tmp_path/'s.json'
    good=FakeFetcher({source.url:page([1])})
    watch(state,[source],good,path,AT,client)
    bad=FakeFetcher({source.url:WatchError('HTTP_ERROR','mock outage')})
    for _ in range(2):
        assert watch(state,[source],bad,path,AT,client)[2]=='sent'
        assert not state['events'] and not state['incidents']
    text=client.send.call_args.args[0][0]['content']['text']
    assert 'HTTP_ERROR' in text and '心跳正常' not in text
    assert watch(state,[source],good,path,AT,client)[2]=='no_changes'
    assert client.send.call_count==2


def test_failed_alert_survives_and_reports_recovery(source,tmp_path):
    state=empty_state()
    path=tmp_path/'s.json'
    good=FakeFetcher({source.url:page([1])})
    watch(state,[source],good,path,AT,dry_run=True)
    client=Mock()
    client.send.side_effect=WatchError('DELIVERY_ERROR','mock failed alert')
    bad=FakeFetcher({source.url:WatchError('HTTP_ERROR','mock outage')})
    with pytest.raises(WatchError): watch(state,[source],bad,path,AT,client)
    state=load_state(path)
    assert state['incidents']
    client.send.side_effect=None
    assert watch(state,[source],good,path,AT,client)[2]=='sent'
    assert '已恢复' in client.send.call_args.args[0][0]['content']['text']
    assert not load_state(path)['incidents']


def test_new_event_retries_without_new_discovery_same_day(source,tmp_path):
    state=empty_state()
    path=tmp_path/'s.json'
    good=FakeFetcher({source.url:page([1])})
    watch(state,[source],good,path,AT,dry_run=True)
    observe(state,[article(source,2)],source,AT)
    state['delivery']['last_success_date']='2026-09-05'
    client=Mock()
    client.send.side_effect=WatchError('DELIVERY_ERROR','mock failed batch')
    with pytest.raises(WatchError): watch(state,[source],good,path,AT,client)
    state=load_state(path)
    client.send.side_effect=None
    assert watch(state,[source],good,path,AT,client)[2]=='sent'
    assert all(e['reported_at'] for e in load_state(path)['events'].values())
    assert watch(state,[source],good,path,AT,client)[2]=='no_changes'
