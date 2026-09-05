import json
import os
import tempfile
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from .models import WatchError


def empty_state():
    return dict(schema_version=1,notices={},events={},sources={},runs=[],delivery={},incidents={})


def validate_state(state):
    try:
        if state['schema_version']!=1:
            raise ValueError()
        for name in ('notices','events','sources','delivery','incidents'):
            if not isinstance(state[name],dict):
                raise ValueError()
        if not isinstance(state['runs'],list):
            raise ValueError()
        for key,n in state['notices'].items():
            if n['id']!=key or not isinstance(n['observations'],dict) or not n['source_ids']:
                raise ValueError()
            if n['site_id'] not in ('physics','jwc','nkzbb') or type(n['revision']) is not int or n['revision']<0:
                raise ValueError()
            if not isinstance(n['title'],str) or not isinstance(n['canonical_url'],str) or sorted(n['observations'])!=sorted(n['source_ids']):
                raise ValueError()
            for observation in n['observations'].values():
                if not isinstance(observation['title'],str) or not isinstance(observation['url'],str):
                    raise ValueError()
            for field in ('first_seen_at','last_observed_at'):
                if datetime.fromisoformat(n[field]).utcoffset() is None:
                    raise ValueError()
        for key,e in state['events'].items():
            if e['event_id']!=key or e['notice_id'] not in state['notices'] or e['type'] not in ('NEW','UPDATED'):
                raise ValueError()
            for field in ('detected_at','reported_at'):
                if e[field] is not None and datetime.fromisoformat(e[field]).utcoffset() is None:
                    raise ValueError()
        for s in state['sources'].values():
            if type(s['initialized']) is not bool or not isinstance(s['page_cache'],dict):
                raise ValueError()
            if type(s['ever_nonempty']) is not bool or type(s['consecutive_failures']) is not int:
                raise ValueError()
            if s['unresolved_frontier'] is not None and not isinstance(s['unresolved_frontier'],list):
                raise ValueError()
            for cached in s['page_cache'].values():
                if not isinstance(cached['items'],list) or type(cached['valid_empty']) is not bool:
                    raise ValueError()
                if cached['next_url'] is not None and not isinstance(cached['next_url'],str):
                    raise ValueError()
                for item in cached['items']:
                    if not all(k in item for k in ('source_id','site_id','title','url','publish_date')):
                        raise ValueError()
        for r in state['runs']:
            if datetime.fromisoformat(r['started_at']).utcoffset() is None or not isinstance(r['source_results'],list):
                raise ValueError()
    except (KeyError,TypeError,ValueError,AttributeError):
        raise WatchError('STATE_ERROR','State is corrupt or schema is unsupported; original file preserved') from None


def load_state(path):
    path=Path(path)
    if not path.exists():
        return empty_state()
    try:
        state=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        raise WatchError('STATE_ERROR','Cannot read state; original file preserved') from None
    validate_state(state)
    return state


def save_state(path,state):
    validate_state(state)
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.state-',suffix='.tmp',delete=False) as f:
            temp=Path(f.name)
            json.dump(state,f,ensure_ascii=False,indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,path)
    except OSError:
        raise WatchError('STATE_ERROR','Atomic state write failed') from None
    finally:
        if temp and temp.exists():
            temp.unlink()


@contextmanager
def state_lock(path):
    lock=Path(str(path)+'.lock')
    lock.parent.mkdir(parents=True,exist_ok=True)
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        raise WatchError('STATE_ERROR','Another process holds state lock; verify before removing stale lock') from None
    try:
        with os.fdopen(fd,'w') as f:
            f.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)
