#!/usr/bin/env python3
"""Apply optional local OCR results, rejecting wrong-set and duplicate card codes."""
import collections,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/catalog.json').read_text());results=json.loads(Path(sys.argv[1]).read_text())
for c in data['cards']:
 candidate=results.get(str((ROOT/c['front']).resolve()),'').replace('‐','-').replace('–','-')
 if re.fullmatch(rf'AP{c["set"]}-\d{{3}}[A-Z]?',candidate):c['code']=candidate;c['codeSource']='ocr'
counts=collections.Counter(c.get('code') for c in data['cards'] if c.get('code'))
for c in data['cards']:
 if counts.get(c.get('code'),0)>1:c['code']='';c.pop('codeSource',None)
data.pop('version',None);data['version']=hashlib.sha256(json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:16]
(ROOT/'data/catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(ROOT/'data/catalog.js').write_text('window.CARD_CATALOG='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'data/version.json').write_text(json.dumps({'version':data['version'],'count':len(data['cards'])},indent=2));print('Numbered',sum(bool(c.get('code')) for c in data['cards']),'/',len(data['cards']))
