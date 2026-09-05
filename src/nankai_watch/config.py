from pathlib import Path
from urllib.parse import urlsplit
import yaml
from lxml import etree
from .models import Source, WatchError

HOSTS = {s: s + '.nankai.edu.cn' for s in ('physics','jwc','nkzbb')}
DEFAULT_CONFIG = Path('config/sources.yaml')


def load_sources(path=DEFAULT_CONFIG):
    try:
        data = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
        if data['schema_version'] != 1 or data['approval_status'] != 'approved':
            raise ValueError()
        result=[]
        seen=set()
        for row in data['sources']:
            if row['source_id'] in seen:
                raise ValueError()
            seen.add(row['source_id'])
            if not row.get('enabled'):
                continue
            if row.get('approval_status') != 'approved' or type(row['allow_empty']) is not bool:
                raise ValueError()
            u=urlsplit(row['url'])
            if u.scheme!='https' or u.hostname!=HOSTS[row['site_id']] or u.username or u.port or u.query or u.fragment:
                raise ValueError()
            if not (u.path.endswith('/list.htm') or u.path.endswith('/index.chtml')):
                raise ValueError()
            selectors=row['selectors']
            for key in ('list_selector','item_selector','title_selector','link_selector','date_selector'):
                etree.XPath(selectors[key])
            result.append(Source(**{key:row[key] for key in Source.__dataclass_fields__}))
        if not result:
            raise ValueError()
        return sorted(result,key=lambda s:(list(HOSTS).index(s.site_id),s.priority,s.source_id))
    except (OSError,KeyError,TypeError,ValueError,yaml.YAMLError,etree.XPathError):
        raise WatchError('CONFIG_ERROR','Invalid or unapproved source registry') from None
