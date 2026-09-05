import re
from urllib.parse import urlsplit, urlunsplit, parse_qs
from .base import ListAdapter, text
from ..models import WatchError

class NkzbbAdapter(ListAdapter):
    def next_page(self,d,url):
        nodes=d.xpath('//td[@class="tright"]')
        match=re.search(r'共(\d+)条.*?此页(\d+)-(\d+)条.*?共(\d+)页.*?此页\s*(\d+)/(\d+)',text(nodes[0]) if len(nodes)==1 else '')
        if not match:
            raise WatchError('PARSE_ERROR','Procurement pagination summary missing')
        total,start,end,pages,current,last=map(int,match.groups())
        u=urlsplit(url)
        expected=int(parse_qs(u.query).get('curPage',['1'])[0])
        if current!=expected or pages!=last or end>total or start!=(current-1)*15+1 or not start<=end:
            raise WatchError('PARSE_ERROR','Procurement returned wrong page')
        if current<pages:
            return urlunsplit((u.scheme,u.netloc,u.path,'curPage='+str(current+1),''))
        return None
