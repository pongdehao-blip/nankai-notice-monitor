from datetime import date
from urllib.parse import urljoin, urlsplit, parse_qs
import re
from lxml import html, etree
from ..models import ParsedItem, ParsedPage, WatchError
from ..normalize import normalize_url, normalize_title


def text(node):
    return normalize_title(node.text_content())


class ListAdapter:
    def get_date(self,node):
        return text(node) or None

    def parse(self,body,source,url):
        try:
            d=html.fromstring(body,parser=html.HTMLParser(encoding='utf-8'))
            spec=source.selectors
            containers=d.xpath(spec['list_selector'])
            if len(containers)!=1:
                if d.xpath('//noscript') and re.search(r'enable javascript|启用.*JavaScript',text(d),re.I):
                    raise WatchError('JS_REQUIRED','List requires JavaScript')
                raise WatchError('PARSE_ERROR','Expected list container missing or ambiguous')
            container=containers[0]
            rows=container.xpath(spec['item_selector'])
            items=[]
            for row in rows:
                titles=row.xpath(spec['title_selector'])
                links=row.xpath(spec['link_selector'])
                dates=row.xpath(spec['date_selector'])
                if len(titles)!=1 or len(links)!=1 or len(dates)>1:
                    raise WatchError('PARSE_ERROR','Article markup changed')
                title=normalize_title(titles[0].get('title') or text(titles[0]))
                href=links[0].get('href','').strip()
                if not title or not href or '\ufffd' in title:
                    raise WatchError('PARSE_ERROR','Article title or link missing')
                published=self.get_date(dates[0]) if dates else None
                if published:
                    date.fromisoformat(published)
                items.append(ParsedItem(source.source_id,source.site_id,title,normalize_url(href,url),published))
            next_url=self.next_page(d,url)
            valid_empty=False
            if not items:
                # A known container must really be empty, not merely fail the row selector.
                blank=not text(container) and not container.xpath('.//a')
                selected=d.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," selected ")]/@href')
                nav_match=any(urlsplit(urljoin(url,u)).path==urlsplit(source.url).path for u in selected)
                heading=d.xpath('//div[@class="page-con-title"]/h2')
                valid_empty=blank and nav_match and bool(heading) and next_url is None
                if not valid_empty:
                    raise WatchError('PARSE_ERROR','Zero items without audited empty structure')
            return ParsedPage(items,next_url,valid_empty)
        except WatchError:
            raise
        except (ValueError,TypeError,IndexError,etree.Error):
            raise WatchError('PARSE_ERROR','Invalid list markup or date') from None

    def next_page(self,d,url):
        matches=d.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," next ") or normalize-space(.)="下一页"]/@href')
        candidates=[urljoin(url,h) for h in matches if re.search(r'/list\d+\.htm$',h)]
        if candidates:
            current=re.search(r'/list(\d*)\.htm$',urlsplit(url).path)
            expected=int(current.group(1) or '1')+1
            for target in candidates:
                if urlsplit(target).hostname!=urlsplit(url).hostname or not target.endswith(f'/list{expected}.htm'):
                    raise WatchError('PARSE_ERROR','Unexpected pagination target')
            return candidates[0]
        # Disabled next buttons are normal, but malformed live hrefs are not.
        if any(h and not h.startswith('javascript:') and h!='#' for h in matches):
            raise WatchError('PARSE_ERROR','Pagination markup changed')
        return None
