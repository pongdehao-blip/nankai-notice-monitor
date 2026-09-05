"""Export checked UTF-8 files for an atomic Git tree publication; no network or credentials."""
import argparse
import json
from check_release import ROOT,release_files

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--index',type=int)
    p.add_argument('--part',type=int)
    args=p.parse_args()
    groups=[]
    batch=[]
    size=0
    for file in release_files():
        content=file.read_text(encoding='utf-8')
        row=dict(path=file.relative_to(ROOT).as_posix(),mode='100644',type='blob',content=content)
        count=len(json.dumps(row,ensure_ascii=False).encode())
        if batch and size+count>100_000:
            groups.append(batch)
            batch=[]
            size=0
        batch.append(row)
        size+=count
    if batch: groups.append(batch)
    if args.index is None:
        print(json.dumps(dict(groups=len(groups),files=sum(map(len,groups)),bytes=sum(f.stat().st_size for f in release_files()))))
    else:
        serialized=json.dumps(groups[args.index],ensure_ascii=False)
        if args.part is None:
            print(json.dumps(dict(parts=(len(serialized)+39999)//40000)))
        else:
            print(json.dumps(serialized[args.part*40000:(args.part+1)*40000],ensure_ascii=False))

if __name__=='__main__':
    main()
