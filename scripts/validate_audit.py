"""Offline artifact acceptance. No network calls."""
from build_audit import *
from datetime import date

STATUSES={'PASS','PASS_EMPTY','REDIRECTED','STRUCTURE_CHANGED','MISSING','NOT_A_LIST','DUPLICATE_SOURCE','JS_REQUIRED','BLOCKED','OUT_OF_SCOPE','ERROR'}

def require(condition,message):
    if not condition:
        raise ValueError(message)

def validate(data,registry,manifest):
    expected={s['source_id'] for s in baseline()}
    ids=[r['source_id'] for r in data['sources']]
    require(data['schema_version']==1,'schema_version')
    require(len(ids)==43 and set(ids)==expected,'All 43 unique baseline IDs required')
    require(datetime.fromisoformat(data['audited_at']).utcoffset() is not None,'Aware audit timestamp')
    require(len(data['entry_sites'])==3,'Three entry sites')
    require({urlsplit(e['url']).hostname for e in data['entry_sites']}==HOSTS,'Entry host coverage')
    require(not data['phase_b_approved'],'Human gate must remain closed')
    for r in data['sources']+data['new_candidate_sources']:
        require(r['audit_status'] in STATUSES,'Unknown status')
        require(datetime.fromisoformat(r['fetched_at']).utcoffset() is not None,'Aware fetch time')
        require(urlsplit(r['candidate_url']).hostname in HOSTS,'Source host')
        require(r['item_count_page1']==len(r['items_page1']),'Item count disagreement')
        require((ROOT/r['fixture_path']).is_file(),'Fixture missing')
        for key in ('list_selector','item_selector','title_selector','link_selector','date_selector'):
            etree.XPath(r[key])
        for item in r['items_page1']+r['pagination']['items_page2']:
            require(bool(item['title'].strip()),'Missing title')
            require(urlsplit(item['url']).scheme in ('https','http'),'Malformed article URL')
            require('\ufffd' not in item['title'],'Corrupt title encoding')
            date.fromisoformat(item['publish_date'])
        if r['audit_status'] in ('PASS','PASS_EMPTY'):
            require(r['http_status']==200 and r['server_rendered'] and r['is_time_series_list'],'PASS evidence missing')
            require(r['pagination']['kind'] in ('path','query','none'),'Unverified pagination cannot PASS')
        if r['audit_status']=='PASS_EMPTY':
            require(not r['items_page1'] and r['allow_empty_observed'],'False empty')
            require(r['empty_evidence']['container_blank'] and r['empty_evidence']['selected_navigation_matches'],'Empty structural evidence')
        if r['pagination']['kind'] in ('path','query'):
            pg=r['pagination']
            require(pg['http_status_page2']==200 and bool(pg['items_page2']),'Page 2 absent')
            require(pg['items_page2']!=r['items_page1'],'Page 2 repeated first page')
            require(urlsplit(pg['page2_url']).hostname==urlsplit(r['final_url']).hostname,'Pagination left host')
    require(len(registry['sources'])==43 and {r['source_id'] for r in registry['sources']}==expected,'Proposed registry coverage')
    require(not registry['production_ready'],'Registry must remain proposed')
    require(all(not r['enabled'] for r in registry['sources']+registry['new_candidate_sources']),'Unapproved source enabled')
    for fixture in manifest.values():
        body=(ROOT/fixture['path']).read_text(encoding='utf-8')
        d,containers,items=parse(body,fixture['site_id'],fixture['url'])
        require(bool(containers),'Fixture does not cover claimed layout')
        require(items==fixture['items'],'Fixture extraction mismatch')
        require(not d.xpath('//script|//input|//iframe'),'Unsanitized fixture')
    # Each source's exact selector is independently applied to its representative layout.
    for r in data['sources']:
        d=html.fromstring((ROOT/r['fixture_path']).read_text(encoding='utf-8'))
        cc=d.xpath(r['list_selector'])
        require(len(cc)==1,'Source representative selector mismatch')
        rows=cc[0].xpath(r['item_selector'])
        require(bool(rows)==bool(r['items_page1']),'Empty/nonempty fixture class mismatch')
        for row in rows:
            require(len(row.xpath(r['title_selector']))==1 and len(row.xpath(r['date_selector']))==1,'Exact selectors not reproducible')
    patterns=[r'https://open\.feishu\.cn/open-apis/bot/v2/hook/[a-zA-Z0-9-]{12,}',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'(?i)(?:authorization|set-cookie|cookie)\s*:\s*\S+',r'(?i)(?:sessionid|jsessionid|access_token)=[^\s"<>]{8,}',r'(?i)_queryspt|_paramspt']
    for folder in ('artifacts','config','tests/fixtures/audit'):
        for p in (ROOT/folder).rglob('*'):
            if p.is_file():
                text=p.read_text(encoding='utf-8')
                for pattern in patterns:
                    require(not re.search(pattern,text),'Potential sensitive material in '+p.name)
    return dict(baseline_ids=len(ids),fixture_replays=len(manifest),all_sources_have_reproducible_selectors=True,security_scan='PASS',phase_b_approved=False)

def main():
    def read(p):
        return json.loads((ROOT/p).read_text(encoding='utf-8'))
    results=validate(read('artifacts/source_audit.json'),read('config/sources.audit-proposed.yaml'),read('artifacts/fixture_manifest.json'))
    results.update(validated_at=now(),status='PASS',meaning='Historical Phase A snapshot validated; current production approval is recorded separately in config/APPROVAL.md')
    dump('artifacts/validation_results.json',results)
    print(json.dumps(results,ensure_ascii=False))

if __name__=='__main__':
    main()
