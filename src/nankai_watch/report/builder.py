import json
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from ..models import Report, WatchError

SITE_LABELS={'physics':'物理科学学院','jwc':'教务部','nkzbb':'招投标管理办公室'}


def payload(text):
    return {'msg_type':'text','content':{'text':text}}


def encoded_size(value):
    return len(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8'))


def split_report(text,day,max_bytes=18000):
    if max_bytes<512:
        raise WatchError('REPORT_ERROR','Report byte cap too small')
    prefix=f'南开通知日报 {day}'
    # Reserve room for a numbered header, then split on Unicode character boundaries.
    budget=max_bytes-128
    parts=[]
    remaining=text
    while remaining:
        lo,hi=1,len(remaining)
        best=0
        while lo<=hi:
            mid=(lo+hi)//2
            if encoded_size(payload(remaining[:mid]))<=budget:
                best=mid
                lo=mid+1
            else:
                hi=mid-1
        if not best:
            raise WatchError('REPORT_ERROR','Cannot split report')
        if best<len(remaining):
            newline=remaining.rfind('\n',0,best)
            if newline>best//2:
                best=newline+1
        parts.append(remaining[:best])
        remaining=remaining[best:]
    parts=parts or ['当前无新增通知。']
    messages=[payload(f'{prefix}（{i}/{len(parts)}）\n'+part) for i,part in enumerate(parts,1)]
    if any(encoded_size(p)>max_bytes for p in messages):
        raise WatchError('REPORT_ERROR','Report chunk exceeds byte cap')
    return messages


def build_report(state,sources,at,max_bytes=18000):
    day=datetime.fromisoformat(at).astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat()
    pending=[e for e in state['events'].values() if e['reported_at'] is None]
    grouped=defaultdict(list)
    for event in pending:
        grouped[event['notice_id']].append(event)
    names={s.source_id:s.name for s in sources}
    lines=[f'本次待报：{len(grouped)} 条通知，{len(pending)} 个变更记录。']
    if not pending:
        lines.append('当前无新增或更新通知，监测心跳正常执行。')
    for site,label in SITE_LABELS.items():
        selected=[(key,events) for key,events in grouped.items() if state['notices'][key]['site_id']==site]
        if not selected:
            continue
        lines+=['',label]
        for key,events in sorted(selected,key=lambda pair:min(e['detected_at'] for e in pair[1])):
            n=state['notices'][key]
            updated=any(e['type']=='UPDATED' for e in events)
            kind='UPDATED 更新' if updated else 'NEW 新增'
            lines += [f'[{kind}] {n["title"]}',
                '栏目：'+' / '.join(names.get(s,s) for s in n['source_ids']),
                '发布日期：'+(n['publish_date'] or '未提供'),n['canonical_url'] or '未提供链接']
            if len(events)>1:
                lines.append(f'合并展示 {len(events)} 个待报变更，以当前已观察版本为准。')
            lines.append('')
    lines+=['','系统健康']
    initialized=sum(bool(state['sources'].get(s.source_id,{}).get('initialized')) for s in sources)
    ok=sum(state['sources'].get(s.source_id,{}).get('last_status')=='OK' for s in sources)
    lines.append(f'来源 {len(sources)} 个，已建立基线 {initialized} 个，本次正常 {ok} 个。')
    if state['runs']:
        newly=sum(r['baseline'] and r['status']=='OK' for r in state['runs'][-1]['source_results'])
        if newly:
            lines.append(f'本次初始化 {newly} 个来源，历史文章不作为新增推送。')
    for s in sources:
        h=state['sources'].get(s.source_id,{})
        if h.get('last_status')!='OK':
            lines.append(f'{s.source_id} {s.name}：{h.get("last_status","未初始化")}；连续异常 {h.get("consecutive_failures",0)} 次。')
    for issue in state['incidents'].values():
        status='已恢复' if issue.get('recovered_at') else '未恢复'
        lines.append(f'待报异常：{issue["source_id"]} {issue["status"]}，{issue["count"]} 次，{status}；首次 {issue["first_at"]}，最近 {issue["last_at"]}。')
    if state['delivery'].get('last_error'):
        lines.append('此前日报投递失败；待报事件已保留，本次补报。')
    return Report(day,split_report('\n'.join(lines),day,max_bytes),[e['event_id'] for e in pending])
