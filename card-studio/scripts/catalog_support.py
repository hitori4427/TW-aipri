"""Merge reviewed supplemental variants without changing official card identities."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SUPPLEMENT_SOURCE = 'https://script.google.com/macros/s/AKfycbzNaO9kOfBLwlfEnqez9WC_eqFO7Tgp_SqEomw3UTG9NJ1EssHRjKsEFHRz9HknSND5/exec'

def validate_supplement(card, official):
    code = card['code']
    if card.get('category') in ('activity','product'):
        key = card['sourceKey']
        if card['uid'] != 'supplement-event-' + hashlib.sha256(key.encode()).hexdigest()[:16] or card['set'] != 'event':
            raise ValueError('Invalid activity identity')
        if card['sourceLabel'] != key or not card['name'] or not card.get('reviewedAt'):
            raise ValueError('Missing activity review')
        if not card.get('back') and card.get('missingBackReason') != 'source-placeholder':
            raise ValueError('Missing back must be explicitly recorded')
    else:
        if not re.fullmatch(r'AP[1-6]-\d{3}P', code):
            raise ValueError('Invalid supplemental card code')
        if card['uid'] != 'supplement-' + code.lower() or card['variant'] != 'P':
            raise ValueError('Invalid supplemental identity')
        base = official[card['relatedUid']]
        if card['baseCode'] != code[:-1] or card['set'] != int(code[2]) or base['set'] != card['set']:
            raise ValueError('Invalid ordinary-card relationship')
        if card['character'] != base['character'] or card['name'] != base['name'] + '（P版）':
            raise ValueError('Supplement does not match its ordinary card')
        if not isinstance(card['signatureVisible'], bool) or not card.get('reviewedAt'):
            raise ValueError('Missing variant review')
    if card['source'] != SUPPLEMENT_SOURCE or card['codeSource'] != 'source-page':
        raise ValueError('Unreviewed supplemental source')
    if not card.get('back') and card.get('missingBackReason') != 'source-placeholder':
        raise ValueError('Missing back must be explicitly recorded')
    for side in ('front', 'back'):
        if side=='back' and not card.get(side):continue
        parsed = urlparse(card['source' + side.title()])
        query = parse_qs(parsed.query)
        if parsed.scheme != 'https' or parsed.netloc != 'drive.google.com' or parsed.path != '/thumbnail' or not re.fullmatch(r'[A-Za-z0-9_-]+', query.get('id', [''])[0]):
            raise ValueError('Invalid supplemental image source')
        if not re.fullmatch(r'assets/cards/supplement-[a-f0-9]{24}\.webp', card[side]):
            raise ValueError('Invalid supplemental image path')
        for field in (side+'SourceSha256', side+'AssetSha256'):
            if not re.fullmatch(r'[a-f0-9]{64}', card[field]):
                raise ValueError('Missing image checksum')

def merge_supplemental(root, cards):
    path = Path(root)/'data/supplemental-cards.json'
    if not path.exists():
        raise ValueError('Reviewed supplemental manifest is missing; refusing catalog update')
    data = json.loads(path.read_text())
    if data['schemaVersion'] != 1:
        raise ValueError('Unsupported supplemental schema')
    official = {c['uid']: c for c in cards if c['uid'].startswith('official-')}
    supplements = {}
    codes = set()
    for card in data['cards']:
        validate_supplement(card, official)
        if card['uid'] in supplements or (card['code'] and card['code'] in codes):
            raise ValueError('Duplicate supplemental identity')
        supplements[card['uid']] = card; codes.add(card['code'])
    previous = {c['uid'] for c in cards if c['uid'].startswith('supplement-')}
    if previous - supplements.keys():
        raise ValueError('Supplemental manifest would remove existing cards')
    return sorted([*official.values(), *supplements.values()], key=lambda c: (7 if c['set']=='event' else c['set'], c['sourceLabel'] if c['set']=='event' else (official[c['relatedUid']]['sourceId'] if 'relatedUid' in c else c['sourceId']), 'relatedUid' in c, c['uid']))

def write_catalog(root, cards):
    root = Path(root)
    payload = {'schemaVersion': 1, 'cards': cards}
    payload['version'] = hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()[:16]
    (root/'data/catalog.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    (root/'data/catalog.js').write_text('window.CARD_CATALOG='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n')
    (root/'data/version.json').write_text(json.dumps({'version':payload['version'],'count':len(cards)},indent=2))
    return payload['version']
