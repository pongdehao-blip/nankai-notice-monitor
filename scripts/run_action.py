"""One-shot Actions coordinator; checkpoints remote state before report delivery."""
import argparse
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from nankai_watch.config import load_sources
from nankai_watch.models import utc_now,WatchError
from nankai_watch.state import state_lock,load_state,save_state
from nankai_watch.crawler import crawl
from nankai_watch.fetcher import Fetcher
from nankai_watch.service import watch
from nankai_watch.report.feishu import FeishuClient
from nankai_watch.report.builder import split_report
from state_branch import prepare,persist


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['crawl','watch','daily'])
    args=p.parse_args()
    path=None
    fetcher=None
    client=None
    state=None
    try:
        sources=load_sources()
        path=prepare('state-data')
        with state_lock(path):
            state=load_state(path)
            fetcher=Fetcher()
            if args.command=='crawl':
                run=crawl(state,sources,fetcher)
                save_state(path,state)
                persist(path.parent)
                outcome='saved'
            else:
                if os.environ.get('FEISHU_WEBHOOK'):
                    client=FeishuClient(os.environ['FEISHU_WEBHOOK'])
                try:
                    run,report,outcome=watch(state,sources,fetcher,path,utc_now(),client=client,checkpoint=lambda:persist(path.parent))
                finally:
                    # On partial delivery failure, pending events and health survive.
                    if path.is_file():
                        persist(path.parent)
            failures=sum(r['status']!='OK' for r in run['source_results'])
            print(json.dumps(dict(command=args.command,delivery=outcome,source_failures=failures,notices=len(state['notices'])),ensure_ascii=False))
            return 2 if failures else 0
    except WatchError as exc:
        if exc.status=='STATE_ERROR' and state is None and args.command in ('watch','daily') and os.environ.get('FEISHU_WEBHOOK'):
            try:
                client=client or FeishuClient(os.environ['FEISHU_WEBHOOK'])
                day=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
                client.send(split_report('系统健康：STATE_ERROR。状态无法安全载入，未重建基线或覆盖原文件，请人工恢复。',day))
            except WatchError:
                pass
        print(json.dumps(dict(status=exc.status,message=str(exc)),ensure_ascii=False))
        return 1
    finally:
        if fetcher: fetcher.close()
        if client: client.close()

if __name__=='__main__':
    raise SystemExit(main())
