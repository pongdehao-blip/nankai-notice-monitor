import sys
from audit_sources import *

for url in sys.argv[1:]:
    r = fetch(url)
    d = html.fromstring(r['html'])
    print(url)
    anchors = d.xpath('//a[contains(@href,"page.htm") or contains(@href,".chtml")][@title]')
    if anchors:
        a = anchors[-1]
        print(html.tostring(a.getparent().getparent(), encoding='unicode')[:6500])
    print(r['html'][-5000:])
