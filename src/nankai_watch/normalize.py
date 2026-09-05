import re
from urllib.parse import urljoin, urlsplit, urlunsplit
from .models import WatchError


def normalize_url(url, base=''):
    u=urlsplit(urljoin(base,url.strip()))
    if u.scheme.lower() not in ('http','https') or not u.hostname or u.username or u.password:
        raise WatchError('PARSE_ERROR','Invalid public article link')
    try:
        port=u.port
    except ValueError:
        raise WatchError('PARSE_ERROR','Invalid public article port') from None
    host=u.hostname.lower()
    netloc=host if port is None or (u.scheme=='https' and port==443) or (u.scheme=='http' and port==80) else f'{host}:{port}'
    path=u.path
    if host=='physics.nankai.edu.cn':
        # Only the presentation variant tested by the approved audit.
        path=re.sub(r'^/_t12/', '/',path)
    return urlunsplit((u.scheme.lower(),netloc,path,u.query,''))


def normalize_title(title):
    return ' '.join(title.split())
