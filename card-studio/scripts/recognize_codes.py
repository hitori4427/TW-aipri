#!/usr/bin/env python3
"""Optional OCR. macOS Vision or Tesseract; retains existing card numbers."""
import json,platform,re,shutil,subprocess,tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/catalog.json').read_text());results={}
with tempfile.TemporaryDirectory() as tmp:
 mapping={}
 for c in data['cards']:
  if c.get('code'):continue
  image=(ROOT/c['front']).resolve()
  with Image.open(image) as im:
   w,h=im.size;crop=im.crop((int(w*.6),0,w,int(h*.12)));crop=crop.resize((crop.width*4,crop.height*4));target=Path(tmp)/(image.stem+'.png');crop.save(target);mapping[str(target)]=str(image)
 if mapping and platform.system()=='Darwin' and shutil.which('swiftc'):
  exe=str(Path(tmp)/'ocr');subprocess.run(['swiftc',str(ROOT/'scripts/recognize_codes.swift'),'-o',exe],check=True);out=subprocess.check_output([exe,*mapping],text=True)
  results={mapping[p]:code for p,code in json.loads(out).items()}
 elif mapping and shutil.which('tesseract'):
  for path,original in mapping.items():
   text=subprocess.check_output(['tesseract',path,'stdout','--psm','6'],text=True,stderr=subprocess.DEVNULL);m=re.search(r'AP\d+[-‐– ]\d{3}[A-Z]?',text)
   if m:results[original]=m.group().replace(' ','-')
 elif mapping:
  print('OCR unavailable; keeping official source IDs');raise SystemExit(0)
 result=Path(tmp)/'results.json';result.write_text(json.dumps(results));subprocess.run(['python3',str(ROOT/'scripts/apply_ocr.py'),str(result)],check=True)
