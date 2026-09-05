"""Package only public release files, excluding caches, environment and runtime state."""
import zipfile
import argparse
import shutil
from pathlib import Path
from check_release import ROOT,release_files,main as validate

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage-checkout',action='store_true')
    args=parser.parse_args()
    validate()
    out=ROOT/'dist/nankai-notice-monitor-v1.zip'
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in release_files():
            archive.write(path,path.relative_to(ROOT).as_posix())
    print(str(out))
    if args.stage_checkout:
        destination=(ROOT/'.deployment').resolve()
        if destination.parent!=ROOT.resolve() or not (destination/'.git').exists():
            raise ValueError('Expected existing isolated deployment checkout')
        for path in release_files():
            target=destination/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target)

if __name__=='__main__':
    main()
