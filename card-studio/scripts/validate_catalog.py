#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
x=json.loads((ROOT/'data/catalog.json').read_text());seen=set();images=0
assert x['schemaVersion']==1 and x['cards']
for c in x['cards']:
 assert c['uid'] not in seen, 'Duplicate official ID';seen.add(c['uid'])
 assert c['name'] and c['source'].startswith('https://aipri.com.tw/cards/')
 for side in ['front','back']:
  if not c.get(side):continue
  p=(ROOT/c[side]).resolve();assert p.is_relative_to(ROOT/'assets/cards'), 'Invalid image path'
  with Image.open(p) as im:
   im.verify()
  images+=1
assert (ROOT/'data/catalog.js').read_text().startswith('window.CARD_CATALOG=')
print(f'Validated {len(seen)} unique cards and {images} decodable images')
