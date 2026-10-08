#!/usr/bin/env python3
"""Create a self-contained offline HTML and zip package from the catalog."""
import base64,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 catalog=json.loads((ROOT/'data/catalog.json').read_text())
 for card in catalog['cards']:
  for side in ('front','back'):
   if card.get(side):card[side]='data:image/webp;base64,'+base64.b64encode((ROOT/card[side]).read_bytes()).decode()
 source=(ROOT/'index.html').read_text();source=source.replace('<link rel="stylesheet" href="style.css">','<style>'+(ROOT/'style.css').read_text()+'</style>');source=source.replace('<link rel="manifest" href="manifest.webmanifest">','')
 source=source.replace('<script src="data/catalog.js"></script>','<script>window.IS_STANDALONE=true;window.CARD_CATALOG='+json.dumps(catalog,ensure_ascii=False).replace('<','\\u003c')+';</script>');source=source.replace('<script src="app.js"></script>','<script>'+(ROOT/'app.js').read_text().replace('</script','<\\/script')+'</script>')
 out=ROOT/'release';out.mkdir(exist_ok=True);html=out/'偶像卡片交換工作室.html';html.write_text(source)
 with zipfile.ZipFile(out/'偶像卡片交換工作室-離線圖庫版.zip','w',zipfile.ZIP_DEFLATED) as z:
  z.write(html,html.name);z.write(ROOT/'使用說明.txt','使用說明.txt')
 print(f'Built {len(catalog["cards"])} cards, {html.stat().st_size/1024/1024:.1f} MB')
if __name__=='__main__':main()
