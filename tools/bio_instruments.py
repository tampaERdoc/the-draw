# -*- coding: utf-8 -*-
"""Fill instrument gaps in existing line-ups from harvested festival-bio prose.

A festival bio is useful in two different ways and the obvious loader only takes one of
them. Where a band has no line-up at all, the bio supplies one, and hand_members.py
handles that. But 1,299 bands DO have a line-up with blank instruments - mostly Discogs,
which returns names only - and for 45 of those a bio names what the same people play.
Discarding those bios because the band "already has members" threw away the instruments.

So this matches on the person's name within the band and fills only what is blank. It
never overwrites an instrument already recorded, and it never adds a person: someone the
bio names who is not in the line-up is skipped, because the line-up came from a source
that knows the membership and the bio may be describing a guest or a former member.

Writes roles rather than instrument, ahead of instruments.py, for the same reason
discogs_instruments.py does: normalising and cross-band propagation still have to run.
"""
import json, os, re, sys, glob, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/home/claude/fest2/work/fests/*.json'

def nkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and '); s = re.sub(r'^(the|a)\s+', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)

def pkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '', s)

def main():
    bios = {}
    for p in glob.glob(SRC):
        if os.path.basename(p) in ('harvest.json',):
            continue
        try:
            recs = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(recs, dict):
            continue
        for v in recs.values():
            if not v.get('members'):
                continue
            k = nkey(v.get('title'))
            d = bios.setdefault(k, {})
            for m in v['members']:
                if m.get('instrument'):
                    d.setdefault(pkey(m['name']), m['instrument'])
    if not bios:
        print('no harvested bios to read'); return

    filled = bands = 0
    for fid in IDS:
        path = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        for b in d['bands']:
            says = bios.get(nkey(b['name']))
            if not says:
                continue
            got = 0
            for m in (b.get('members') or []):
                if m.get('instrument') or m.get('roles'):
                    continue
                inst = says.get(pkey(m.get('name')))
                if inst:
                    m['roles'] = [inst]
                    got += 1
            if got:
                filled += got; bands += 1
        json.dump(d, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('festival bios filled %d blank instruments across %d existing line-ups'
          % (filled, bands))

if __name__ == '__main__':
    main()
