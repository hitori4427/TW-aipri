#!/usr/bin/env python3
"""Download the official public card catalog. Existing assets are reused; no deletes."""
import argparse, concurrent.futures, hashlib, io, json, re, time, urllib.request
from pathlib import Path
from PIL import Image
from catalog_support import merge_supplemental, write_catalog
ROOT=Path(__file__).resolve().parents[1]
def fetch(url):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CardStudio/1.0'}),timeout=40) as r:return r.read()
  except Exception:
   if attempt==2:raise
   time.sleep(attempt+1)
def parse(html):
 match=re.search(r'id="__NUXT_DATA__">(.*?)</script>',html,re.S)
 if not match:raise ValueError('Official page format changed: missing catalog JSON')
 values=json.loads(match.group(1));memo={}
 def decode(i):
  if i<0:return None
  if i in memo:return memo[i]
  v=values[i]
  if isinstance(v,dict):
   out={};memo[i]=out;out.update({k:decode(n) for k,n in v.items()});return out
  if isinstance(v,list):
   if v and isinstance(v[0],str):return decode(v[1]) if len(v)>1 and isinstance(v[1],int) else None
   out=[];memo[i]=out;out.extend(decode(n) for n in v);return out
  return v
 for i,v in enumerate(values):
  if isinstance(v,dict) and 'cards' in v and 'title' in v:return decode(i)
 raise ValueError('Official page format changed: cards not found')
def asset(url):
 name=hashlib.sha256(url.encode()).hexdigest()[:24]+'.webp';path=ROOT/'assets/cards'/name
 if not path.exists():
  raw=fetch(url)
  with Image.open(io.BytesIO(raw)) as im:
   im.thumbnail((720,1100));tmp=path.with_suffix('.tmp');im.save(tmp,'WEBP',quality=88,method=4);tmp.replace(path)
 return 'assets/cards/'+name

def main():
 p=argparse.ArgumentParser();p.add_argument('--sets',nargs='+',type=int,default=[1,2,3,4,5,6]);args=p.parse_args()
 target=ROOT/'data/catalog.json';previous=json.loads(target.read_text()) if target.exists() else {'cards':[]};old={c['uid']:c for c in previous['cards']};allcards=dict(old);errors=[]
 (ROOT/'assets/cards').mkdir(parents=True,exist_ok=True)
 for season in args.sets:
  url=f'https://aipri.com.tw/cards/{season}';data=parse(fetch(url).decode());items=data['cards'];print(f'Set {season}: {len(items)} cards',flush=True)
  if not items:raise ValueError('Empty catalog; refusing update')
  def process(pair):
   n,c=pair;uid=f'official-{c["id"]}';prev=old.get(uid,{})
   return {'uid':uid,'code':prev.get('code',''),'codeSource':prev.get('codeSource',''),'catalogLabel':f'第{season}彈 · 官方ID {c["id"]}','name':c['outfit_name'],'character':c['character_name'],'rarity':c['level'],'set':season,'front':asset(c['image']),'back':asset(c['back_image']) if c.get('back_image') else None,'sourceFront':c['image'],'sourceBack':c.get('back_image'),'source':url,'sourceId':c['id']}
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   futures=[pool.submit(process,x) for x in enumerate(items)]
   for f in concurrent.futures.as_completed(futures):
    try:c=f.result();allcards[c['uid']]=c
    except Exception as e:errors.append(str(e))
  print(f'Set {season}: downloaded',flush=True)
 if errors:raise RuntimeError('Incomplete sync; prior catalog retained: '+str(errors[:5]))
 cards=merge_supplemental(ROOT,list(allcards.values()))
 version=write_catalog(ROOT,cards)
 print(f'Catalog ready: {len(cards)} cards, version {version}',flush=True)
if __name__=='__main__':main()
