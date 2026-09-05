"""Git infrastructure only. Never force-push or merge machine state blindly."""
import os
import subprocess
from pathlib import Path
from nankai_watch.models import WatchError


def git(*args,cwd=None,input=None,check=True):
    result=subprocess.run(['git',*args],cwd=cwd,input=input,text=True,encoding='utf-8',capture_output=True)
    if check and result.returncode:
        raise WatchError('STATE_ERROR','Git state operation failed; no force overwrite attempted')
    return result


def prepare(directory):
    directory=Path(directory).resolve()
    root=Path.cwd().resolve()
    if directory.parent!=root or directory.name!='state-data' or directory.exists():
        raise WatchError('STATE_ERROR','State checkout must be a fresh state-data directory in the repository')
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    remote=git('ls-remote','--exit-code','--heads','origin','state',check=False)
    if remote.returncode==0:
        git('fetch','--depth=1','origin','refs/heads/state:refs/remotes/origin/state')
        commit=git('rev-parse','refs/remotes/origin/state').stdout.strip()
        fresh=False
    elif remote.returncode==2:
        tree=git('hash-object','-w','-t','tree','--stdin',input='').stdout.strip()
        commit=git('commit-tree',tree,'-m','Initialize public notice state').stdout.strip()
        fresh=True
    else:
        raise WatchError('STATE_ERROR','Cannot check remote state branch; refusing to initialize')
    git('worktree','add','--detach',str(directory),commit)
    if not fresh and not (directory/'state.json').is_file():
        raise WatchError('STATE_ERROR','Existing state branch lacks state.json; manual recovery required')
    return directory/'state.json'


def persist(directory):
    directory=Path(directory)
    if not (directory/'state.json').is_file():
        raise WatchError('STATE_ERROR','No state snapshot to persist')
    git('add','--','state.json',cwd=directory)
    diff=git('diff','--cached','--quiet',cwd=directory,check=False)
    if diff.returncode==1:
        git('commit','-m','Update public notice state',cwd=directory)
    elif diff.returncode!=0:
        raise WatchError('STATE_ERROR','Cannot compare state changes')
    # An intervening writer causes rejection; never force-push or rebase state.
    git('push','origin','HEAD:refs/heads/state',cwd=directory)
