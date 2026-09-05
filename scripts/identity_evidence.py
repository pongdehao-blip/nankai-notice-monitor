"""Inspect document title metadata only, never article bodies or attachments."""
from build_audit import *

def main():
    result=json.loads((ROOT/'artifacts/source_audit.json').read_text(encoding='utf-8'))
    groups=defaultdict(list)
    for r in result['sources']:
        for i in r['items_page1']+r['pagination']['items_page2']:
            if r['site_id']!='nkzbb' and re.search(REGEX,urlsplit(i['url']).path) and urlsplit(i['url']).hostname in HOSTS:
                groups[identity(i,r['site_id'])].append(dict(i,source_id=r['source_id']))
    pairs=[]
    for key,items in groups.items():
        urls=list(dict.fromkeys(i['url'] for i in items))
        if len(urls)>1:
            pairs.append(dict(identity=key,observations=items))
    probes=[]
    for site in ['physics','jwc']:
        pair=next((p for p in pairs if p['identity'].startswith(site+':')),None)
        original=(pair['observations'][0]['url'] if pair else next(r for r in result['sources'] if r['site_id']==site)['items_page1'][0]['url'])
        split=urlsplit(original)
        urls=[original,split.scheme+'://'+split.netloc+'/_t12'+split.path]
        if pair:
            urls.append(next(i['url'] for i in pair['observations'] if i['url']!=original))
        for u in urls:
            # Explicitly bounded, no redirect following; fetch no linked resources.
            time.sleep(.7)
            out=dict(site_id=site,url=u,fetched_at=now(),http_status=None,title=None)
            try:
                with OPENER.open(Request(u,headers={'User-Agent':UA}),timeout=18) as response:
                    out['http_status']=response.status
                    raw=response.read(2_000_000)
                    d=html.fromstring(raw)
                    out['title']=' '.join(d.xpath('//title/text()'))
            except (HTTPError,URLError,TimeoutError,OSError) as exc:
                out['http_status']=getattr(exc,'code',None)
                out['error']=type(exc).__name__
            probes.append(out)
            print(site,out['http_status'],out['title'],flush=True)
    dump('artifacts/identity_evidence.json',dict(regex=REGEX,cross_source_observations=pairs,title_metadata_probes=probes,scope='Title metadata only. No article-body or attachment analysis. Template equivalence limited to tested examples.'))

if __name__=='__main__':
    main()
