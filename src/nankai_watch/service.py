from .crawler import crawl
from .state import save_state
from .report.builder import build_report
from .models import WatchError


def daily(state,sources,fetcher,state_path,at,client=None,dry_run=False,max_pages=3,force_report=False,checkpoint=None):
    run=crawl(state,sources,fetcher,max_pages=max_pages,at=at)
    # Durable capture before any network delivery, including missing webhook failure.
    save_state(state_path,state)
    if checkpoint:
        checkpoint()  # Infrastructure boundary: durable remote capture before sending.
    report=build_report(state,sources,at)
    if dry_run:
        return run,report,'dry_run'
    if not force_report and state['delivery'].get('last_success_date')==report.day:
        return run,report,'already_sent'
    try:
        if client is None:
            raise WatchError('DELIVERY_ERROR','FEISHU_WEBHOOK is not configured')
        client.send(report.payloads)
    except WatchError:
        state['delivery']['last_error']='DELIVERY_ERROR'
        state['delivery']['last_attempt_at']=at
        save_state(state_path,state)
        raise
    # This point is reachable only after every chunk was acknowledged.
    for key in report.event_ids:
        state['events'][key]['reported_at']=at
    state['incidents'].clear()
    state['delivery'].update(last_success_date=report.day,last_success_at=at,last_error=None,last_attempt_at=at)
    save_state(state_path,state)
    return run,report,'sent'
