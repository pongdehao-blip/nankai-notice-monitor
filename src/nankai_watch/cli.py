import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from .config import load_sources
from .state import state_lock,load_state,save_state
from .fetcher import Fetcher
from .crawler import crawl
from .models import WatchError,utc_now
from .service import watch
from .report.feishu import FeishuClient
from .report.builder import split_report


def arguments(argv=None):
    p=argparse.ArgumentParser(description='南开官网通知采集与按需推送；不解析正文或附件')
    p.add_argument('command',choices=['crawl','watch','daily'])
    p.add_argument('--state-path',required=True,type=Path)
    p.add_argument('--config',default='config/sources.yaml',type=Path)
    p.add_argument('--max-pages',type=int,default=3,help='每来源最大页数，溢出恢复时可显式提高，范围 1–100')
    p.add_argument('--dry-run',action='store_true',help='采集并保存状态，但不发送、不标记已报告')
    p.add_argument('--report-path',type=Path,help='保存本次通知 JSON 预览')
    p.add_argument('--force-report',action='store_true',help='无变化也显式发送心跳；不会重发已确认的事件')
    a=p.parse_args(argv)
    if not 1<=a.max_pages<=100:
        p.error('--max-pages must be 1..100')
    return a


def main(argv=None):
    args=arguments(argv)
    client=None
    fetcher=None
    at=utc_now()
    try:
        sources=load_sources(args.config)
        with state_lock(args.state_path):
            state=load_state(args.state_path)
            fetcher=Fetcher()
            if args.command=='crawl':
                run=crawl(state,sources,fetcher,max_pages=args.max_pages,at=at)
                save_state(args.state_path,state)
                delivery='not_scheduled'
            else:
                if not args.dry_run and os.environ.get('FEISHU_WEBHOOK'):
                    client=FeishuClient(os.environ['FEISHU_WEBHOOK'])
                run,report,delivery=watch(state,sources,fetcher,args.state_path,at,client,args.dry_run,args.max_pages,args.force_report)
                if args.report_path:
                    args.report_path.parent.mkdir(parents=True,exist_ok=True)
                    args.report_path.write_text(json.dumps(report.payloads,ensure_ascii=False,indent=2),encoding='utf-8')
            failures=sum(r['status']!='OK' for r in run['source_results'])
            print(json.dumps(dict(command=args.command,sources=len(sources),notices=len(state['notices']),pending_events=sum(e['reported_at'] is None for e in state['events'].values()),source_failures=failures,delivery=delivery),ensure_ascii=False))
            return 2 if failures else 0
    except WatchError as exc:
        # A corrupt state must not be replaced with a new baseline.
        if exc.status=='STATE_ERROR' and args.command in ('watch','daily') and not args.dry_run and os.environ.get('FEISHU_WEBHOOK'):
            try:
                client=client or FeishuClient(os.environ['FEISHU_WEBHOOK'])
                day=datetime.fromisoformat(at).astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat()
                client.send(split_report('系统健康：STATE_ERROR。原状态文件已保留，请人工恢复；本次未重新建立基线。',day))
            except WatchError:
                pass
        print(json.dumps(dict(status=exc.status,message=str(exc)),ensure_ascii=False))
        return 1
    finally:
        if fetcher:
            fetcher.close()
        if client:
            client.close()

if __name__=='__main__':
    raise SystemExit(main())
