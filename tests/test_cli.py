import json
from conftest import FakeFetcher,page
from nankai_watch import cli
from nankai_watch.state import load_state

def test_cli_dry_run_without_secret(source,tmp_path,monkeypatch,capsys):
    monkeypatch.delenv('FEISHU_WEBHOOK',raising=False)
    monkeypatch.setattr(cli,'load_sources',lambda _: [source])
    monkeypatch.setattr(cli,'Fetcher',lambda:FakeFetcher({source.url:page([1,2,3])}))
    path=tmp_path/'state.json'
    report=tmp_path/'preview.json'
    assert cli.main(['daily','--state-path',str(path),'--dry-run','--report-path',str(report)])==0
    assert not load_state(path)['events']
    assert json.loads(report.read_text(encoding='utf-8'))
    assert 'dry_run' in capsys.readouterr().out
