from unittest.mock import Mock
import pytest
import requests
from nankai_watch.fetcher import Fetcher
from nankai_watch.models import WatchError

def response(status=200,body=b'<html/>',headers=None):
    r=Mock(status_code=status,headers=headers or {'Content-Type':'text/html'})
    r.__enter__=Mock(return_value=r)
    r.__exit__=Mock(return_value=False)
    r.iter_content.return_value=iter([body])
    return r

def test_fetcher_polite_retry_and_conditional_headers():
    session=Mock()
    session.get.side_effect=[response(404),requests.Timeout(),response(304)]
    sleep=Mock()
    f=Fetcher(session,sleep=sleep)
    assert f.fetch('https://physics.nankai.edu.cn/572/list.htm',etag='abc').status==304
    assert session.get.call_args.kwargs['headers']['If-None-Match']=='abc'
    assert session.get.call_args.kwargs['allow_redirects'] is False
    assert sleep.call_count==3

def test_fetcher_blocks_external_redirect_before_request():
    session=Mock()
    session.get.side_effect=[response(404),response(302,headers={'Location':'https://evil.example/a'})]
    f=Fetcher(session,sleep=lambda _:None)
    with pytest.raises(WatchError,match='redirect'):
        f.fetch('https://physics.nankai.edu.cn/572/list.htm')
    assert session.get.call_count==2

def test_fetcher_robots_denial():
    session=Mock()
    session.get.return_value=response(200,b'User-agent: *\nDisallow: /')
    f=Fetcher(session,sleep=lambda _:None)
    with pytest.raises(WatchError) as caught:
        f.fetch('https://physics.nankai.edu.cn/572/list.htm')
    assert caught.value.status=='BLOCKED' and session.get.call_count==1

@pytest.mark.parametrize('error,status',[(requests.Timeout(),'TIMEOUT'),(requests.ConnectionError('sensitive text'),'HTTP_ERROR')])
def test_fetcher_failure_redaction(error,status):
    session=Mock()
    session.get.side_effect=error
    with pytest.raises(WatchError) as caught:
        Fetcher(session,retries=0,sleep=lambda _:None).fetch('https://physics.nankai.edu.cn/572/list.htm')
    assert caught.value.status==status and 'sensitive' not in str(caught.value)
