"""Record the user's 2026-09-05 explicit Phase A decisions, preserving audit history."""
import json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def main():
    audit=json.loads((ROOT/'artifacts/source_audit.json').read_text(encoding='utf-8'))
    result={'schema_version':1,'approval_status':'approved','approval_record':'config/APPROVAL.md','sources':[]}
    for r in audit['sources']+audit['new_candidate_sources']:
        result['sources'].append(dict(source_id=r['source_id'],site_id=r['site_id'],name=r.get('proposed_name',r['name']),url=r['candidate_url'],source_type=r['source_type'],priority=r['priority'],allow_empty=r['source_id'] in ('J09','J10','J13','J14'),allow_empty_baseline=r['allow_empty_baseline'],enabled=True,approval_status='approved',layout_group=r['layout_group'],selectors={k:r[k] for k in ('list_selector','item_selector','title_selector','date_selector','link_selector')},audit_status=r['audit_status']))
    (ROOT/'config/sources.yaml').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
