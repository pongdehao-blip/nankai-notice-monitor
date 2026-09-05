def source_health():
    return dict(initialized=False,last_success_at=None,last_status='UNINITIALIZED',last_item_count=0,consecutive_failures=0,last_error=None,ever_nonempty=False,page_cache={},unresolved_frontier=None)


def record_health(state,source_id,status,count,at,error=None):
    h=state['sources'].setdefault(source_id,source_health())
    h.update(last_status=status,last_item_count=count,last_error=error)
    if status=='OK':
        h.update(last_success_at=at,consecutive_failures=0)
        for issue in state['incidents'].values():
            if issue['source_id']==source_id and issue.get('recovered_at') is None:
                issue['recovered_at']=at
    else:
        h['consecutive_failures']+=1
        key=source_id+':'+status
        issue=state['incidents'].setdefault(key,dict(source_id=source_id,status=status,first_at=at,last_at=at,count=0,recovered_at=None))
        issue.update(last_at=at,count=issue['count']+1,recovered_at=None)
