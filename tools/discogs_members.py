# -*- coding: utf-8 -*-
"""Attach the Discogs line-ups to bands MusicBrainz had nothing on.

Discogs knows a lot of small punk bands MusicBrainz has never heard of. It gives names
only - no instruments - so these members arrive without one and pick one up from
tools/instruments.py if the same person plays elsewhere in the database.

Only fills bands that have no line-up. A MusicBrainz line-up carries instruments and
years, so it is always the better record and is never overwritten.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/home/claude/fest2/work/dg/members.json'

def nkey(s):
    import re, unicodedata
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and '); s = re.sub(r'^(the|a)\s+', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)

def main():
    if not os.path.exists(SRC):
        print('no Discogs data yet'); return
    dg = json.load(open(SRC, encoding='utf-8'))
    filled = people = contested = 0
    for fid in IDS:
        p = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        for b in d['bands']:
            if b.get('members'):
                continue                      # MusicBrainz wins: it knows instruments
            rec = dg.get(nkey(b['name']))
            if not rec or not rec.get('members'):
                if rec:
                    b['member_source'] = ('Not found — Discogs lists no members for this band'
                                          if not rec.get('note') else
                                          'Not found — no MusicBrainz or Discogs entry')
                continue
            b['members'] = [{'name': m['name'], 'discogs_id': m.get('discogs_id'),
                             'roles': [], 'begin': '', 'end': '',
                             'current': m.get('current', True), 'source': 'Discogs'}
                            for m in rec['members']]
            b['member_names'] = ', '.join(m['name'] for m in b['members'])
            b['member_count'] = len(b['members'])
            b['member_source'] = 'Discogs'
            b['member_source_url'] = rec.get('url') or ''
            if (rec.get('namesakes') or 1) > 1:
                note = ('Line-up taken from one of %d Discogs artists sharing this name; '
                        'identity not independently confirmed.' % rec['namesakes'])
                if note not in (b.get('flags') or ''):
                    b['flags'] = ((b.get('flags') or '') + ' ' + note).strip()
                contested += 1
            filled += 1
            people += len(b['members'])
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Discogs line-ups attached to %d bands (%d people); %d flagged as contested names'
          % (filled, people, contested))

if __name__ == '__main__':
    main()
