# -*- coding: utf-8 -*-
"""Put an instrument on the people Discogs gave us by name only.

The Discogs artist endpoint returns a members array with no instruments, so 97% of the
2,080 people it contributed arrived blank - and a blank person can never turn up in an
instrument search, which is the whole point of the people index.

The instruments are one level down, in each release's extraartists roles.
/home/claude/fest2/dg_credits.py collects them; this writes them on.

It writes to roles rather than instrument, so that instruments.py - which runs after -
still does the normalising and still gets to propagate a person's instrument to the
other bands they play in. Nothing already carrying an instrument is touched.
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/home/claude/fest2/work/dg/credits.json'

def pkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '', s)

def main():
    if not os.path.exists(SRC):
        print('no Discogs credits collected yet'); return
    # one person may appear under several bands; a name maps to one instrument
    byname = {}
    for rec in json.load(open(SRC, encoding='utf-8')).values():
        for nm, inst in (rec.get('instruments') or {}).items():
            byname.setdefault(pkey(nm), inst)
    if not byname:
        print('Discogs credits file holds no instruments yet'); return

    filled = 0
    for fid in IDS:
        path = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        for b in d['bands']:
            for m in (b.get('members') or []):
                if m.get('instrument') or m.get('roles'):
                    continue
                inst = byname.get(pkey(m.get('name')))
                if inst:
                    m['roles'] = [inst]
                    filled += 1
        json.dump(d, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Discogs release credits gave an instrument to %d member records '
          '(%d distinct people)' % (filled, len(byname)))

if __name__ == '__main__':
    main()
