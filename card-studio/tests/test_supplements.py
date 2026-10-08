import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from catalog_support import merge_supplemental
import sync_catalog

class SupplementsTest(unittest.TestCase):
 def setUp(self):
  self.data=json.loads((ROOT/'data/catalog.json').read_text())['cards']
  self.manifest=json.loads((ROOT/'data/supplemental-cards.json').read_text())
 def test_merge_is_repeatable_and_preserves_official_records(self):
  merged=merge_supplemental(ROOT,self.data)
  self.assertEqual(merge_supplemental(ROOT,merged),merged)
  original={c['uid']:c for c in self.data if c['uid'].startswith('official-')}
  self.assertEqual(original,{c['uid']:c for c in merged if c['uid'].startswith('official-')})
  self.assertEqual(sum(c.get('variant')=='P' for c in merged),28)
  self.assertEqual(sum(c.get('set')=='event' for c in merged),23)
  self.assertEqual(sum(c.get('missingBackReason')=='source-placeholder' for c in merged),4)
 def test_partial_official_sync_keeps_supplemental_records(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir()
   for name in ['catalog.json','supplemental-cards.json']:(root/'data'/name).write_text((ROOT/'data'/name).read_text())
   official=[c for c in self.data if c['uid'].startswith('official-') and c['set']==1]
   page={'cards':[dict(id=c['sourceId'],outfit_name=c['name'],character_name=c['character'],level=c['rarity'],image=c['sourceFront'],back_image=c['sourceBack']) for c in official]}
   assets={c['source'+s.title()]:c[s] for c in official for s in ['front','back']}
   with patch.object(sync_catalog,'ROOT',root),patch.object(sync_catalog,'fetch',return_value=b''),patch.object(sync_catalog,'parse',return_value=page),patch.object(sync_catalog,'asset',side_effect=lambda u:assets[u]),patch.object(sys,'argv',['sync_catalog.py','--sets','1']):sync_catalog.main()
   updated=json.loads((root/'data/catalog.json').read_text())['cards']
   normalize=lambda cards:{c['uid']:{**c,'codeSource':c.get('codeSource','')} for c in cards}
   self.assertEqual(normalize(self.data),normalize(updated))
 def test_missing_manifest_and_deleted_supplement_are_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir()
   with self.assertRaises(ValueError):merge_supplemental(root,self.data)
   data=copy.deepcopy(self.manifest);data['cards'].pop()
   (root/'data/supplemental-cards.json').write_text(json.dumps(data))
   with self.assertRaises(ValueError):merge_supplemental(root,self.data)
 def test_placeholder_and_wrong_relation_are_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir()
   for bad in ['placeholder','relation']:
    data=copy.deepcopy(self.manifest)
    if bad=='placeholder':data['cards'][0]['sourceBack']='https://placehold.co/400x600?text=BACK'
    else:data['cards'][0]['relatedUid']='official-2'
    (root/'data/supplemental-cards.json').write_text(json.dumps(data))
    with self.assertRaises(ValueError):merge_supplemental(root,self.data)
if __name__=='__main__':unittest.main()
