"""Rebuild catalog from reviewed local supplemental data; no network requests."""
import json
from pathlib import Path
from catalog_support import merge_supplemental, write_catalog
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    cards=merge_supplemental(ROOT,json.loads((ROOT/'data/catalog.json').read_text())['cards'])
    version=write_catalog(ROOT,cards)
    print(f'Catalog ready: {len(cards)} cards, version {version}')
