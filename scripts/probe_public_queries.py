from build_audit import *
results=[]
for site_path in ['cghw/index.chtml','yxgk/index.chtml']:
    url='https://nkzbb.nankai.edu.cn/'+site_path+'?curPage=2'
    r=fetch(url)
    d,cc,ii=parse(r['html'],'nkzbb',url)
    results.append(dict(url=url,http_status=r['http_status'],fetched_at=r['fetched_at'],items=ii,pagination_text=d.xpath('//td[@class="tright"]/text()')))
    print(url,r['http_status'],len(ii),results[-1]['pagination_text'],flush=True)
dump('artifacts/nkzbb_query_probe.json',results)
