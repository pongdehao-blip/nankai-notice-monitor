import json
import pytest
from nankai_watch.state import empty_state,load_state,save_state,state_lock
from nankai_watch.models import WatchError

def test_state_missing_and_atomic_windows_path(tmp_path):
    path=tmp_path/'中文目录'/'state.json'
    state=load_state(path)
    save_state(path,state)
    assert load_state(path)==state
    assert not list(path.parent.glob('*.tmp'))

@pytest.mark.parametrize('data',['{broken',json.dumps({'schema_version':999})])
def test_corrupted_state_preserved(tmp_path,data):
    path=tmp_path/'state.json'
    path.write_text(data)
    with pytest.raises(WatchError): load_state(path)
    assert path.read_text()==data

def test_state_lock(tmp_path):
    path=tmp_path/'state.json'
    with state_lock(path):
        with pytest.raises(WatchError):
            with state_lock(path): pass
    assert not path.with_suffix('.json.lock').exists()
