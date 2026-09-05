"""Phase A public-source audit only; never sends messages or runs a monitor."""
import json
import re
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from urllib.robotparser import RobotFileParser
from lxml import html, etree

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.audit-cache'
HOSTS = {'physics.nankai.edu.cn', 'jwc.nankai.edu.cn', 'nkzbb.nankai.edu.cn'}
UA = 'NankaiNoticeWatch-Audit/1.0 (public list metadata audit; low rate)'

def now():
    return datetime.now(timezone.utc).isoformat()

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = build_opener(NoRedirect())

def fetch(url):
    """No cookies/auth; check every redirect BEFORE requesting its target."""
    CACHE.mkdir(exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()
    path = CACHE / (key + '.json')
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    host = urlsplit(url).hostname
    if host not in HOSTS or urlsplit(url).scheme not in ('http', 'https'):
        raise ValueError('Outside public host allowlist')
    result = dict(requested_url=url, final_url=url, fetched_at=now(), redirects=[], http_status=None, content_type=None, html='', error=None)
    rp = RobotFileParser()
    if urlsplit(url).path != '/robots.txt':
        policy = fetch('https://' + host + '/robots.txt')
        if policy['http_status'] == 200:
            rp.parse(policy['html'].splitlines())
        elif policy['http_status'] in (404,410):
            rp.allow_all = True
        else:
            rp.disallow_all = True
    else:
        rp.allow_all = True
    for hop in range(6):
        if not rp.can_fetch(UA, result['final_url']):
            result['error'] = 'Robots policy prevents probe'
            break
        time.sleep(0.7)
        try:
            response = OPENER.open(Request(result['final_url'], headers={'User-Agent': UA}), timeout=18)
        except HTTPError as exc:
            response = exc
        except (URLError, TimeoutError, OSError) as exc:
            result['error'] = type(exc).__name__
            break
        with response:
            result['http_status'] = response.code
            result['content_type'] = response.headers.get('Content-Type', '')
            if response.code in (301,302,303,307,308):
                target = urljoin(result['final_url'], response.headers.get('Location', ''))
                result['redirects'].append({'from': result['final_url'], 'to': target, 'status':response.code})
                if urlsplit(target).hostname != host or urlsplit(target).scheme not in ('http','https') or urlsplit(target).username:
                    result['error'] = 'Cross-host or unsafe redirect not followed'
                    break
                result['final_url'] = target
                continue
            raw = response.read(3_000_001)
            if len(raw) > 3_000_000:
                result['error'] = 'Response exceeds audit size cap'
                break
            charset = re.search(br'charset=["\x27 ]*([\w-]+)', raw[:4096], re.I)
            encoding = charset.group(1).decode() if charset else (response.headers.get_content_charset() or 'utf-8')
            result['html'] = raw.decode(encoding, errors='replace')
            break
    else:
        result['error'] = 'Redirect limit'
    # Cache only sanitized public HTML, never response headers or cookies.
    if result['html'] and 'html' in (result['content_type'] or ''):
        doc = html.fromstring(result['html'])
        result['public_pagination_endpoints'] = sorted(set(re.findall(r'/(?:\w+/)+icGg\.chtml', result['html'])))
        result['pagination_field_names'] = doc.xpath('//form[@id="dataForm1"]//input/@name')
        for node in doc.xpath('//script|//style|//comment()|//input|//iframe|//img'):
            node.getparent().remove(node)
        for node in doc.iter():
            for attr in list(node.attrib):
                if attr not in ('class','id','href','title'):
                    del node.attrib[attr]
        result['html'] = html.tostring(doc, encoding='unicode')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

def baseline():
    return json.loads((ROOT/'source_baseline.json').read_text(encoding='utf-8'))['sources']

def collect():
    policies = {}
    for host in sorted(HOSTS):
        r = fetch('https://' + host + '/robots.txt')
        rp = RobotFileParser()
        if r['http_status'] == 200:
            rp.parse(r['html'].splitlines())
        elif r['http_status'] in (404,410):
            rp.allow_all = True
        else:
            rp.disallow_all = True
        policies[host] = rp
        print(host, 'robots', r['http_status'], flush=True)
    urls = ['https://' + h + '/' for h in sorted(HOSTS)] + [s['candidate_url'] for s in baseline()]
    for url in urls:
        if not policies[urlsplit(url).hostname].can_fetch(UA, url):
            print('POLICY_BLOCKED', url, flush=True)
            continue
        r = fetch(url)
        print(r['http_status'], url, r['error'] or '', flush=True)

if __name__ == '__main__':
    collect()
