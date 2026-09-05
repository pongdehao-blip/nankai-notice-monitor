"""Build review artifacts from bounded live probes, with offline replay support."""
from audit_sources import *
from collections import Counter, defaultdict
import argparse

def cls(name):
    return "contains(concat(' ',normalize-space(@class),' '),' " + name + " ')"

LAYOUTS = {
    'physics': dict(list_selector='//*[@id="wp_news_w6"]', item_selector='.//li['+cls('news')+']', title_selector='.//span[@class="news_title"]/a', date_selector='.//span[@class="news_meta"]', link_selector='.//span[@class="news_title"]/a'),
    'jwc': dict(list_selector='//div[@class="page-con-list-news"]', item_selector='./div[@class="item"]', title_selector='./div[@class="t"]/a', date_selector='./div[@class="d"]', link_selector='./div[@class="t"]/a'),
    'nkzbb': dict(list_selector='//*[@id="datab"]', item_selector='./dd', title_selector='./a', date_selector='./span[@class="date"]', link_selector='./a'),
}
LAYOUTS['jwc-simple'] = dict(LAYOUTS['jwc'], list_selector='//div[@class="page-con-list-news1"]')
LAYOUTS['nkzbb-intent'] = dict(LAYOUTS['nkzbb'], list_selector='//dl[@class="llist"]')
REGEX = r'/c\d+a(\d+)/page\.htm$'

def txt(node):
    return ' '.join(node.text_content().split())

def parse(body, site, url):
    d = html.fromstring(body or '<html/>')
    spec = layout(d,site)
    containers = d.xpath(spec['list_selector'])
    items = []
    for container in containers:
        for row in container.xpath(spec['item_selector']):
            aa = row.xpath(spec['link_selector'])
            dates = row.xpath(spec['date_selector'])
            if not aa:
                raise ValueError('Missing article link')
            a = aa[0]
            date = txt(dates[0]) if dates else None
            if site == 'jwc' and dates:
                day = dates[0].xpath('./div[@class="d-d"]')
                month = dates[0].xpath('./div[@class="d-m"]')
                date = txt(month[0]).replace('/','-') + '-' + txt(day[0]) if day and month else date
            items.append(dict(title=a.get('title') or txt(a), url=urljoin(url,a.get('href','')), publish_date=date))
    return d, containers, items

def layout(d,site):
    if site == 'jwc' and d.xpath('//div[@class="page-con-list-news1"]'):
        return LAYOUTS['jwc-simple']
    if site == 'nkzbb' and not d.xpath('//*[@id="datab"]'):
        return LAYOUTS['nkzbb-intent']
    return LAYOUTS[site]

def identity(item, site):
    m = re.search(REGEX, urlsplit(item['url']).path)
    own_host = urlsplit(item['url']).hostname == site + '.nankai.edu.cn'
    return site + ':' + (m.group(1) if m and site != 'nkzbb' and own_host else item['url'].split('#')[0])

def links(d, url):
    result = {}
    for a in d.xpath('//a[@href]'):
        target = urljoin(url,a.get('href'))
        if urlsplit(target).scheme not in ('https','http'):
            continue
        if '/list.htm' in target or '/index.chtml' in target:
            target = target.replace('http://','https://').split('#')[0]
            result.setdefault(target, txt(a))
    return result

def audit(s, fixtures):
    r = fetch(s['candidate_url'])
    site = s['site_id']
    d, containers, items = parse(r['html'],site,r['final_url'])
    rec = dict(s, **{k:r[k] for k in ('final_url','http_status','content_type','fetched_at','redirects')},
        audit_status='ERROR', server_rendered=bool(containers), is_time_series_list=bool(items),
        allow_empty_observed=False, item_count_page1=len(items), sample_titles=[i['title'] for i in items[:3]],
        sample_dates=[i['publish_date'] for i in items[:3]], items_page1=items, **layout(d,site),
        selector_language='XPath', layout_group=site, article_identity=dict(method='canonical_url' if site=='nkzbb' else 'webplus_article_id',regex=None if site=='nkzbb' else REGEX,samples=[i['url'] for i in items[:3]]),
        detail_url_pattern='/category/numeric.chtml' if site=='nkzbb' else REGEX,
        duplicate_source_candidates=[], js_required=False, fixture_path=None, warnings=[], notes='')
    page_links = d.xpath('//a[@href][contains(@href,"list2.htm")]/@href')
    pg = dict(kind='path' if page_links else 'none', page1_url=r['final_url'], page2_url=urljoin(r['final_url'],page_links[0]) if page_links else None, page_size_observed=len(items), items_page2=[], evidence='')
    if page_links:
        rr = fetch(pg['page2_url'])
        _, cc, ii = parse(rr['html'],site,rr['final_url'])
        pg.update(http_status_page2=rr['http_status'],items_page2=ii, page2_fetched_at=rr['fetched_at'], transformation='list.htm -> list{n}.htm', evidence='Live page-2 link followed; same layout verified')
        if rr['http_status'] != 200 or not cc or not ii or ii == items:
            pg['kind']='unknown'
    if site == 'nkzbb':
        pg['page2_url']=r['final_url']+'?curPage=2'
        rr=fetch(pg['page2_url'])
        dd,cc,ii=parse(rr['html'],site,rr['final_url'])
        proof=' '.join(dd.xpath('//td[@class="tright"]/text()')).strip()
        verified=rr['http_status']==200 and bool(cc) and bool(ii) and ii!=items and bool(re.search(r'16-\d+条',proof)) and '2/' in proof
        pg.update(kind='query' if verified else 'unknown',http_status_page2=rr['http_status'],items_page2=ii,page2_fetched_at=rr['fetched_at'],transformation='index.chtml?curPage={n}',evidence=proof,
            note='UI uses POST/AJAX; ordinary public GET curPage=2 independently returns page 2 with correct range and different items. No opaque form fields, cookies or generated ms fields needed.')
    rec['pagination'] = pg
    dates = [i['publish_date'] for i in items]
    pg['strict_descending_observed'] = all(a >= b for a,b in zip(dates,dates[1:]) if a and b)
    pg['cross_page_duplicate_urls'] = sorted({i['url'] for i in items} & {i['url'] for i in pg['items_page2']})
    if not pg['strict_descending_observed']:
        rec['warnings'].append('Nonchronological ordering / possible sticky item: frontier must not stop on first known item')
    if any(urlsplit(i['url']).hostname != urlsplit(r['final_url']).hostname for i in items):
        rec['warnings'].append('External article links observed; do not fetch external destinations')
    if len({identity(i,site) for i in items}) != len(items):
        rec['warnings'].append('Duplicate identity within page')
    if r['http_status'] == 200 and containers:
        if items:
            rec['audit_status'] = 'PASS' if pg['kind'] != 'unknown' else 'STRUCTURE_CHANGED'
        else:
            total = d.xpath('//em[@class="all_count"]/text()')
            pager = d.xpath('//*[@id="wp_pager"]')
            label = d.xpath('//span[@class="Column_Anchor"]|//div[@class="page-con-title"]/h2')
            selected = d.xpath('//a['+cls('selected')+']/@href')
            selected_here = any(urljoin(r['final_url'],u)==r['final_url'] for u in selected)
            genuinely_blank = all(not txt(c) and not c.xpath('.//a') for c in containers)
            valid_empty = bool(label) and (total == ['0'] or bool(pager) or (selected_here and genuinely_blank)) and not page_links
            rec.update(audit_status='PASS_EMPTY' if valid_empty else 'STRUCTURE_CHANGED',allow_empty_observed=valid_empty,is_time_series_list=valid_empty)
            rec['empty_evidence'] = dict(selected_navigation_matches=selected_here,container_blank=genuinely_blank,column_heading=[txt(x) for x in label],older_page_links=page_links)
            rec['notes'] = 'Recognized empty container + matching selected navigation + column heading; no older-page/archive link within column. Current emptiness only, not proof of perpetual emptiness.' if valid_empty else 'Zero extraction is NOT proof of an empty source; needs review'
    elif r['http_status'] in (404,410):
        rec['audit_status']='MISSING'
    elif r['http_status'] in (401,403,429):
        rec['audit_status']='BLOCKED'
    else:
        rec['notes']=r['error'] or 'No recognized list layout'
    if r['redirects'] and rec['audit_status'] in ('PASS','PASS_EMPTY'):
        rec['audit_status']='REDIRECTED'
    if s['source_id'] in ('P02','P03','P09'):
        rec['warnings'].append('Mixed news explicitly accepted by frozen product policy')
    variant = next(k for k,v in LAYOUTS.items() if v == layout(d,site))
    group = variant + ('-empty' if not items else '-list') + ('-single' if not page_links and site!='nkzbb' else '')
    if group not in fixtures:
        p = ROOT/'tests/fixtures/audit'/ (group+'.html')
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(r['html'],encoding='utf-8')
        fixtures[group] = dict(path=p.relative_to(ROOT).as_posix(),source_id=s['source_id'],url=r['final_url'],items=items,site_id=site, fetched_at=r['fetched_at'])
    rec['fixture_path']=fixtures[group]['path']
    rec['fixture_is_representative']=fixtures[group]['source_id'] != s['source_id']
    rec['layout_group']=group
    rec['column_heading']=[txt(x) for x in d.xpath('//div[@class="page-con-title"]/h2|//span[@class="Column_Anchor"]|//dl[@class="llist"]/dt')]
    return rec

def main():
    fixtures={}
    records=[]
    for s in baseline():
        rec=audit(s,fixtures)
        records.append(rec)
        print(s['source_id'],rec['audit_status'],rec['item_count_page1'],flush=True)
    entries=[]
    discovered={}
    known={s['candidate_url'] for s in baseline()}
    for host in sorted(HOSTS):
        url='https://'+host+'/'
        r=fetch(url)
        d=html.fromstring(r['html'])
        nav=links(d,url)
        entries.append(dict(url=url, http_status=r['http_status'], fetched_at=r['fetched_at'], navigation=[dict(url=u,name=n) for u,n in nav.items()], external_links=sorted(set(urljoin(url,a) for a in d.xpath('//a/@href') if urlsplit(urljoin(url,a)).scheme in ('https','http') and urlsplit(urljoin(url,a)).hostname!=host))))
        for u,n in nav.items():
            if urlsplit(u).hostname==host and u not in known:
                discovered[u]=n
    (ROOT/'artifacts').mkdir(exist_ok=True)
    dump('artifacts/discovery_navigation.json',discovered)
    dump('artifacts/fixture_manifest.json',fixtures)
    result=dict(schema_version=1,audited_at=now(),entry_sites=entries,sources=records,new_candidate_sources=[],summary=dict(Counter(r['audit_status'].lower() for r in records)))
    dump('artifacts/source_audit.json',result)

def dump(path,obj):
    (ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
