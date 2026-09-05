import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_audit import ROOT,parse,identity,html
from validate_audit import validate

def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=read('artifacts/source_audit.json')
        cls.registry=read('config/sources.audit-proposed.yaml')
        cls.manifest=read('artifacts/fixture_manifest.json')

    def fixture(self,path,site):
        return parse((ROOT/'tests/fixtures/audit'/path).read_text(encoding='utf-8'),site,'https://'+site+'.nankai.edu.cn/')[2]

    def test_artifact_acceptance(self):
        validate(self.data,self.registry,self.manifest)

    def test_duplicate_id_rejected(self):
        data=copy.deepcopy(self.data)
        data['sources'][-1]=data['sources'][0]
        with self.assertRaisesRegex(ValueError,'43 unique'):
            validate(data,self.registry,self.manifest)

    def test_unapproved_enabled_rejected(self):
        registry=copy.deepcopy(self.registry)
        registry['new_candidate_sources'][0]['enabled']=True
        with self.assertRaisesRegex(ValueError,'Unapproved'):
            validate(self.data,registry,self.manifest)

    def test_unknown_pagination_cannot_pass(self):
        data=copy.deepcopy(self.data)
        data['sources'][0]['pagination']['kind']='unknown'
        with self.assertRaisesRegex(ValueError,'pagination'):
            validate(data,self.registry,self.manifest)

    def test_jwc_split_date_and_sticky(self):
        items=self.fixture('J01-page1.html','jwc')
        self.assertEqual(items[0]['title'],'南开大学2026-2027学年第一学期本科生选课通知')
        self.assertEqual(items[0]['publish_date'],'2026-08-17')
        self.assertEqual(items[1]['publish_date'],'2026-09-04')

    def test_physics_display_date_not_path_date(self):
        items=self.fixture('physics-list.html','physics')
        row=next(i for i in items if '601400' in i['url'])
        self.assertIn('/2026/0823/',row['url'])
        self.assertEqual(row['publish_date'],'2026-08-24')

    def test_procurement_full_title_not_truncated(self):
        items=self.fixture('nkzbb-intent-list.html','nkzbb')
        self.assertEqual(len(items),15)
        self.assertTrue(items[1]['title'].endswith('（2026年第115批）'))
        self.assertNotIn('...',items[1]['title'])

    def test_short_last_page(self):
        self.assertEqual(len(self.fixture('Z04-page2.html','nkzbb')),12)

    def test_valid_empty_vs_broken_container(self):
        body=(ROOT/'tests/fixtures/audit/jwc-simple-empty-single.html').read_text(encoding='utf-8')
        _,cc,items=parse(body,'jwc','https://jwc.nankai.edu.cn/')
        self.assertTrue(cc)
        self.assertEqual(items,[])
        _,cc,_=parse(body.replace('page-con-list-news1','broken-container'),'jwc','https://jwc.nankai.edu.cn/')
        self.assertFalse(cc)

    def test_observed_cross_category_identity(self):
        evidence=read('artifacts/identity_evidence.json')
        pair=evidence['cross_source_observations'][0]
        ids={identity(i,'physics') for i in pair['observations']}
        self.assertEqual(len(ids),1)
        other=dict(pair['observations'][0],url='https://physics.nankai.edu.cn/2026/0101/c572a999999/page.htm')
        self.assertNotIn(identity(other,'physics'),ids)

if __name__=='__main__':
    unittest.main()
