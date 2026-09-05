from dataclasses import asdict
from datetime import datetime,timedelta
import math
import uuid
from .adapters import ADAPTERS
from .models import ParsedItem, ParsedPage, WatchError, utc_now
from .identity import notice_id
from .events import observe
from .health import source_health, record_health


def known_frontier(items,known):
    flags=[notice_id(i) in known for i in items]
    tail=min(3,len(flags))
    return bool(flags) and sum(flags)>=math.ceil(len(flags)*.5) and all(flags[-tail:])


def crawl(state,sources,fetcher,max_pages=3,baseline_pages=2,at=None,scheduled_at=None):
    at=at or utc_now()
    run=dict(run_id=str(uuid.uuid4()),scheduled_at=scheduled_at or at,started_at=at,finished_at=None,source_results=[])
    for source in sources:
        h=state['sources'].setdefault(source.source_id,source_health())
        baseline=not h['initialized']
        previous_known={key for key,n in state['notices'].items() if source.source_id in n['source_ids']}
        known=set(h['unresolved_frontier']) if h['unresolved_frontier'] is not None else previous_known
        cap=baseline_pages if baseline else max_pages
        url=source.url
        items=[]
        visited=set()
        status='OK'
        error=None
        try:
            for page_number in range(1,cap+1):
                if url in visited:
                    raise WatchError('PARSE_ERROR','Pagination loop detected')
                visited.add(url)
                cache=h['page_cache'].get(url)
                result=fetcher.fetch(url,etag=cache.get('etag') if cache else None,last_modified=cache.get('last_modified') if cache else None)
                if result.status==304:
                    if cache is None:
                        raise WatchError('PARSE_ERROR','304 without verified parsed page cache')
                    page=ParsedPage([ParsedItem(**i) for i in cache['items']],cache['next_url'],cache['valid_empty'])
                else:
                    page=ADAPTERS[source.site_id].parse(result.body,source,result.url)
                if not page.items and (not source.allow_empty or h['ever_nonempty'] or page_number!=1):
                    raise WatchError('EMPTY_UNEXPECTED','Previously nonempty or required list returned zero items')
                h['page_cache'][url]=dict(etag=result.etag or (cache or {}).get('etag') if result.status==304 else result.etag,last_modified=result.last_modified or (cache or {}).get('last_modified') if result.status==304 else result.last_modified,items=[asdict(i) for i in page.items],next_url=page.next_url,valid_empty=page.valid_empty)
                items.extend(page.items)
                if page.items:
                    h['ever_nonempty']=True
                if not page.next_url or (not baseline and known_frontier(page.items,known)):
                    h['unresolved_frontier']=None
                    break
                if page_number==cap:
                    if not baseline:
                        h['unresolved_frontier']=sorted(known)
                        raise WatchError('OVERFLOW_RISK','Page limit reached before original known frontier; use a larger bounded recovery run')
                    break
                url=page.next_url
            h['initialized']=True
        except WatchError as exc:
            status,error=exc.status,str(exc)
        except Exception:
            # An unexpected parser/config bug is observable and cannot skip subsequent sources.
            status,error='PARSE_ERROR','Unexpected source processing failure'
        unique={notice_id(i):i for i in reversed(items)}
        observe(state,list(unique.values()),source,at,baseline=baseline)
        record_health(state,source.source_id,status,len(unique),at,error)
        # Bound parsed conditional cache to this run. Notice history and pending events remain intact.
        h['page_cache']={u:v for u,v in h['page_cache'].items() if u in visited}
        run['source_results'].append(dict(source_id=source.source_id,status=status,item_count=len(unique),pages=len(visited),baseline=baseline,error=error))
    run['finished_at']=utc_now()
    state['runs'].append(run)
    cutoff=datetime.fromisoformat(at)-timedelta(days=7)
    state['runs']=[r for r in state['runs'] if datetime.fromisoformat(r['started_at'])>=cutoff][-100:]
    return run
