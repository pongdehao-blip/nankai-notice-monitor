import hashlib
import json
from .identity import notice_id
from .normalize import normalize_url


def observe(state,items,source,at,baseline=False):
    """Compare each source with its own prior observation, preventing stale cross-column oscillation."""
    changed=set()
    for item in items:
        key=notice_id(item)
        n=state['notices'].get(key)
        observation=dict(title=item.title,publish_date=item.publish_date,url=normalize_url(item.url) if item.url else '',priority=source.priority)
        event_type=None
        if n is None:
            n=dict(id=key,site_id=item.site_id,title=item.title,canonical_url=observation['url'],publish_date=item.publish_date,source_ids=[],first_seen_at=at,last_observed_at=at,observations={},revision=0)
            state['notices'][key]=n
            if not baseline:
                event_type='NEW'
        previous=n['observations'].get(source.source_id)
        if previous and (previous['title'],previous['publish_date'])!=(observation['title'],observation['publish_date']):
            if not baseline:
                event_type='UPDATED'
        n['observations'][source.source_id]=observation
        n['source_ids']=sorted(n['observations'])
        n['last_observed_at']=at
        if event_type or len(n['observations'])==1:
            n.update(title=observation['title'],publish_date=observation['publish_date'])
        # Keep the first official link: category/template aliases must not flap URLs.
        if event_type:
            n['revision']+=1
            eid=hashlib.sha256(f'{key}|{n["revision"]}|{event_type}'.encode()).hexdigest()
            state['events'][eid]=dict(event_id=eid,notice_id=key,type=event_type,detected_at=at,reported_at=None,title=observation['title'],publish_date=observation['publish_date'])
            changed.add(eid)
    return changed
