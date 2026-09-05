from .base import ListAdapter, text
from ..models import WatchError

class JwcAdapter(ListAdapter):
    def get_date(self,node):
        day=node.xpath('./div[@class="d-d"]')
        month=node.xpath('./div[@class="d-m"]')
        if day or month:
            if len(day)!=1 or len(month)!=1:
                raise WatchError('PARSE_ERROR','Split date markup changed')
            return text(month[0]).replace('/','-')+'-'+text(day[0]).zfill(2)
        return super().get_date(node)
