import os
from pathlib import Path
import subprocess
import pytest
from state_branch import prepare,persist
from nankai_watch.state import empty_state,save_state
from nankai_watch.models import WatchError

def run(*args,cwd):
    return subprocess.run(['git',*args],cwd=cwd,check=True,capture_output=True,text=True).stdout.strip()

def test_state_branch_initialization_and_conflict(tmp_path,monkeypatch):
    remote=tmp_path/'remote.git'
    run('init','--bare',str(remote),cwd=tmp_path)
    repo=tmp_path/'repo'
    run('init',str(repo),cwd=tmp_path)
    run('config','user.name','Test',cwd=repo)
    run('config','user.email','test@example.invalid',cwd=repo)
    (repo/'README.md').write_text('test')
    run('add','README.md',cwd=repo)
    run('commit','-m','initial',cwd=repo)
    run('remote','add','origin',str(remote),cwd=repo)
    monkeypatch.chdir(repo)
    path=prepare('state-data')
    save_state(path,empty_state())
    persist(path.parent)
    sha=run('rev-parse','refs/heads/state',cwd=remote)
    assert run('ls-tree','--name-only',sha,cwd=remote)=='state.json'
    competitor=tmp_path/'competitor'
    run('clone','--branch','state',str(remote),str(competitor),cwd=tmp_path)
    run('config','user.name','Test',cwd=competitor)
    run('config','user.email','test@example.invalid',cwd=competitor)
    (competitor/'note.txt').write_text('concurrent writer')
    run('add','note.txt',cwd=competitor)
    run('commit','-m','concurrent',cwd=competitor)
    run('push','origin','state',cwd=competitor)
    state=empty_state()
    state['delivery']['last_error']='TEST'
    save_state(path,state)
    with pytest.raises(WatchError): persist(path.parent)
    assert 'note.txt' in run('ls-tree','--name-only','refs/heads/state',cwd=remote)
