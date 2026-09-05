import json
import pytest
from conftest import ROOT
from nankai_watch.config import load_sources
from nankai_watch.models import WatchError

def test_approved_registry(sources):
    assert len(sources)==47
    assert {s.source_id for s in sources if s.allow_empty}=={'J09','J10','J13','J14'}
    assert next(s for s in sources if s.source_id=='J21').url.endswith('/ddpj/list.htm')
    assert not any(s.url.endswith('/533/list.htm') for s in sources)
    assert {s.source_id for s in sources if s.source_id.startswith('C')}=={'C01','C02','C03','C04'}

@pytest.mark.parametrize('change',['duplicate','external','unapproved'])
def test_invalid_registry(tmp_path,change):
    data=json.loads((ROOT/'config/sources.yaml').read_text(encoding='utf-8'))
    if change=='duplicate': data['sources'].append(data['sources'][0])
    if change=='external': data['sources'][0]['url']='https://news.nankai.edu.cn/list.htm'
    if change=='unapproved': data['approval_status']='pending'
    p=tmp_path/'sources.yaml'
    p.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(WatchError): load_sources(p)
