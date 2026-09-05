from build_audit import *

# Bounded navigation inspection. Static/archive links retained with exclusion reasons.
JWC_PARENTS={'bkzs','kcyjc','kcjs','zyjs_36051','tsxxk','tmyjs','bylwwsjw','xkjs','cxcy','sxsj','yywz','jcjsygl','kcszjs','sjys','kcddypj','kcsz','bjrc'}
PHYSICS_CHECK={'535','536','547','blzhsy_29154','533','jlfw','xgdt','jyxx','txgz','25026','sysaq','bksjx','yjsjx','kywws','jxkyg','qtry','575','25031','PR26'}

def main():
    nav=json.loads((ROOT/'artifacts/discovery_navigation.json').read_text(encoding='utf-8'))
    output=[]
    for u,n in nav.items():
        site=urlsplit(u).hostname.split('.')[0]
        slug=urlsplit(u).path.split('/')[1]
        inspect=(site=='jwc' and slug in JWC_PARENTS) or (site=='physics' and slug in PHYSICS_CHECK) or (site=='nkzbb' and slug=='pgt')
        if not inspect:
            output.append(dict(url=u,name=n,decision='excluded_or_static_navigation',reason='Outside frozen notice-stream scope: navigation, ordinary news, archives, downloads, static service pages; not enabled'))
            continue
        r=fetch(u)
        d,cc,ii=parse(r['html'],site,u)
        sub=links(d,u)
        output.append(dict(url=u,name=n,http_status=r['http_status'],fetched_at=r['fetched_at'],item_count=len(ii),items=ii,subnavigation=[dict(url=a,name=b) for a,b in sub.items() if a not in nav],decision='review',enabled=False))
        print(site,n,len(ii),flush=True)
    dump('artifacts/discovery_inspection.json',output)

if __name__=='__main__':
    main()
