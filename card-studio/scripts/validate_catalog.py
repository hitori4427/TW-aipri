import hashlib,json
from pathlib import Path
from PIL import Image
from catalog_support import merge_supplemental
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'data/catalog.json').read_text());seen=set();pairs=set();images=0;missing=[]
assert x['schemaVersion']==1 and x['cards']
assert x['cards']==merge_supplemental(ROOT,x['cards']), 'Catalog and reviewed manifest differ'
for c in x['cards']:
 assert c['uid'] not in seen, 'Duplicate card ID';seen.add(c['uid'])
 assert c['name']
 if c['uid'].startswith('official-'):assert c['source'].startswith('https://aipri.com.tw/cards/')
 pair=(c['front'],c.get('back'));assert pair not in pairs, 'Duplicate image pair';pairs.add(pair)
 for side in ['front','back']:
  if not c.get(side):
   if c['uid'].startswith('supplement-'):assert side=='back' and c['missingBackReason']=='source-placeholder';missing.append(c['code'])
   continue
  p=(ROOT/c[side]).resolve();assert p.is_relative_to(ROOT/'assets/cards'), 'Invalid image path'
  with Image.open(p) as im:im.verify()
  if c['uid'].startswith('supplement-'):
   assert hashlib.sha256(p.read_bytes()).hexdigest()==c[side+'AssetSha256'], 'Supplemental asset changed since review'
   with Image.open(p) as im:assert im.width>=250 and im.height>=350, 'Unexpected supplemental thumbnail'
  images+=1
js=(ROOT/'data/catalog.js').read_text();assert js.startswith('window.CARD_CATALOG=')
assert json.loads(js[len('window.CARD_CATALOG='):].rstrip(';\n'))==x
version=json.loads((ROOT/'data/version.json').read_text());assert version==dict(version=x['version'],count=len(seen))
print(f'Validated {len(seen)} unique cards and {images} decodable images; missing backs: {missing}')
