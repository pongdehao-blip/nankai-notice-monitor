import re
import time
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser
import requests
from .config import HOSTS
from .models import FetchResult, WatchError

UA='NankaiNoticeWatch/1.0 (public university notice lists; low-rate monitoring)'


class Fetcher:
    def __init__(self,session=None,delay=.7,retries=2,sleep=time.sleep):
        self.session=session or requests.Session()
        self.session.trust_env=False  # Never read netrc credentials or ambient proxy credentials.
        self.delay=delay
        self.retries=retries
        self.sleep=sleep
        self.robots={}

    def close(self):
        self.session.close()

    def _request(self,url,headers,host):
        current=url
        for hop in range(6):
            u=urlsplit(current)
            if u.scheme!='https' or u.hostname!=host or u.username or u.port:
                raise WatchError('HTTP_ERROR','Unsafe or external redirect blocked')
            policy=self.robots.get(host)
            if policy and not policy.can_fetch(UA,current):
                raise WatchError('BLOCKED','Site robots policy disallows this list')
            for attempt in range(self.retries+1):
                self.sleep(self.delay if attempt==0 else min(2**attempt,8))
                self.session.cookies.clear()
                try:
                    response=self.session.get(current,headers={'User-Agent':UA,**headers},timeout=(15,15),allow_redirects=False,stream=True)
                except requests.Timeout:
                    if attempt<self.retries:
                        continue
                    raise WatchError('TIMEOUT','Public site request timed out') from None
                except requests.RequestException:
                    if attempt<self.retries:
                        continue
                    raise WatchError('HTTP_ERROR','Public site connection failed') from None
                if response.status_code in (429,500,502,503,504) and attempt<self.retries:
                    response.close()
                    continue
                break
            with response:
                if response.status_code in (301,302,303,307,308):
                    current=urljoin(current,response.headers.get('Location',''))
                    # Validate before following on the next loop; never send conditional headers to another host.
                    continue
                status=response.status_code
                if status not in (200,304,404,410):
                    raise WatchError('BLOCKED' if status in (401,403,429) else 'HTTP_ERROR','Public site HTTP '+str(status))
                chunks=[]
                size=0
                for chunk in response.iter_content(65536):
                    size+=len(chunk)
                    if size>3_000_000:
                        raise WatchError('HTTP_ERROR','List response exceeds size cap')
                    chunks.append(chunk)
                if status==200 and not current.endswith('/robots.txt') and 'html' not in response.headers.get('Content-Type','').lower():
                    raise WatchError('PARSE_ERROR','List response is not HTML')
                def safe_header(name):
                    value=response.headers.get(name)
                    return value if value and len(value)<512 and '\r' not in value and '\n' not in value else None
                return FetchResult(current,status,b''.join(chunks),safe_header('ETag'),safe_header('Last-Modified'))
        raise WatchError('HTTP_ERROR','Redirect limit exceeded')

    def fetch(self,url,etag=None,last_modified=None):
        host=urlsplit(url).hostname
        if host not in HOSTS.values():
            raise WatchError('HTTP_ERROR','Source host not approved')
        if host not in self.robots:
            result=self._request('https://'+host+'/robots.txt',{},host)
            parser=RobotFileParser()
            if result.status in (404,410):
                parser.allow_all=True
            elif result.status==200:
                parser.parse(result.body.decode('utf-8',errors='replace').splitlines())
            else:
                raise WatchError('BLOCKED','Cannot verify robots policy')
            self.robots[host]=parser
        if not self.robots[host].can_fetch(UA,url):
            raise WatchError('BLOCKED','Site robots policy disallows this list')
        headers={}
        if etag:
            headers['If-None-Match']=etag
        if last_modified:
            headers['If-Modified-Since']=last_modified
        result=self._request(url,headers,host)
        if result.status in (404,410):
            raise WatchError('HTTP_ERROR','Public source missing')
        return result
