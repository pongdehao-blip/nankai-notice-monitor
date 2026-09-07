"""Offline workflow/config/sensitive-data checks before publication."""
import json
import re
from pathlib import Path
import yaml
from nankai_watch.config import load_sources

ROOT=Path(__file__).resolve().parents[1]
FOLDERS=('src','scripts','tests','config','artifacts','.github')

def release_files():
    files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ('.md','.toml','.txt')]
    files.append(ROOT/'.gitignore')
    files.append(ROOT/'source_baseline.json')
    for name in FOLDERS:
        files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    return sorted(files)

def main():
    sources=load_sources(ROOT/'config/sources.yaml')
    assert len(sources)==47
    workflows={p.stem:yaml.safe_load(p.read_text(encoding='utf-8')) for p in (ROOT/'.github/workflows').glob('*.yml')}
    for name in ('crawl','daily-report'):
        w=workflows[name]
        triggers=w.get('on',w.get(True)) # YAML 1.1 parsers interpret `on` as Boolean.
        if name=='crawl':
            assert triggers['schedule']==[{'cron':'42 2,5,8,11,14,17,20,23 * * *','timezone':'Asia/Shanghai'}]
        else:
            assert 'schedule' not in triggers
        assert 'workflow_dispatch' in triggers
        assert w['permissions']=={'contents':'write'}
        assert w['concurrency']=={'group':'nankai-notice-state','cancel-in-progress':False}
        assert all(job['runs-on']=='ubuntu-latest' for job in w['jobs'].values())
        delivery_steps=[step for job in w['jobs'].values() for step in job['steps'] if step.get('run')=='python scripts/run_action.py watch']
        assert len(delivery_steps)==1
        assert delivery_steps[0]['env']['FEISHU_WEBHOOK']=='${{ secrets.FEISHU_WEBHOOK }}'
    patterns=[r'https://open\.feishu\.cn/open-apis/bot/v2/hook/[A-Za-z0-9-]{20,}',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'(?i)Authorization:\s*(?:Bearer|Basic)\s+[A-Za-z0-9/+_=.-]{12,}',r'(?i)(?:Cookie|Set-Cookie):\s*[^\s]{12,}']
    files=release_files()
    for p in files:
        content=p.read_text(encoding='utf-8')
        if any(re.search(pattern,content) for pattern in patterns):
            raise ValueError('Possible credential in '+p.relative_to(ROOT).as_posix())
    print(json.dumps(dict(status='PASS',approved_sources=len(sources),workflow_files=len(workflows),scanned_files=len(files),secrets_found=0)))

if __name__=='__main__':
    main()
