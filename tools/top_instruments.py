# -*- coding: utf-8 -*-
"""Attach researched instruments to people a line-up already names.

The top of the index had the opposite problem to the tail. These bands have their
rosters - they are well known enough to be graded - but 298 of their people came from
MusicBrainz with the instrument attribute simply absent, so they were invisible to the
instrument search that the index exists to answer. Only 20 of 66 A+ bands had a line-up
where everyone's instrument was known.

So this is not a line-up source. It only fills instruments for people already present,
matched by name within the band, and it will not add anyone.

It also carries a researched correction to membership: where a source says someone has
left and the record does not say so, the record is updated and the source recorded, so
the former-member filter in the people search has something to work with.

Writes roles rather than instrument, ahead of instruments.py, like the other fillers.
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/home/claude/fest2/work/top/result_aplus.json'

# Rosters research found to be wrong at source, not merely incomplete. Clearing one is
# safer than leaving it: a plausible-looking line-up for the wrong band is worse than
# none, because nothing about it looks suspect.
WRONG_ROSTER = {
    'Cardinals': ('The roster held The Cardinals, the 1950s Baltimore doo-wop group, not '
                  'this Cork indie band. Cleared; needs rebuilding from source.'),
}
# Member entries that are parsing artefacts rather than people.
DROP_MEMBER = re.compile(r'\(principals\)|^\s*$|/.*\(')

def nkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and '); s = re.sub(r'^(the|a)\s+', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)

def pkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '', s)

def main():
    if not os.path.exists(SRC):
        print('no top-grade research to read'); return
    says = {}
    for r in json.load(open(SRC, encoding='utf-8')):
        d = says.setdefault(nkey(r['name']), {})
        for p in (r.get('people') or []):
            d[pkey(p['name'])] = (p.get('instrument') or '', bool(p.get('former')),
                                  r.get('source') or '')

    filled = lefts = dropped = cleared = 0
    for fid in IDS:
        path = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        for b in d['bands']:
            note = WRONG_ROSTER.get(b.get('name'))
            if note and b.get('members'):
                b['members'] = []; b['member_names'] = ''; b['member_count'] = 0
                b['member_source'] = ''; b['member_source_url'] = ''
                if note not in (b.get('flags') or ''):
                    b['flags'] = ((b.get('flags') or '') + ' ' + note).strip()
                cleared += 1
                continue
            ms = b.get('members') or []
            keep = [m for m in ms if not DROP_MEMBER.search(m.get('name') or '')]
            if len(keep) != len(ms):
                dropped += len(ms) - len(keep)
                b['members'] = ms = keep
                b['member_names'] = ', '.join(m['name'] for m in ms)
                b['member_count'] = len(ms)
            told = says.get(nkey(b['name']))
            if not told:
                continue
            for m in ms:
                got = told.get(pkey(m.get('name')))
                if not got:
                    continue
                inst, former, src = got
                if inst and not m.get('instrument') and not m.get('roles'):
                    m['roles'] = [inst]; filled += 1
                # a researched departure the record does not know about
                if former and m.get('current') is not False:
                    m['current'] = False
                    m['left_source'] = src
                    lefts += 1
        json.dump(d, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('top-grade research: %d instruments filled, %d members marked as having left, '
          '%d artefact entries dropped, %d wrong rosters cleared'
          % (filled, lefts, dropped, cleared))

if __name__ == '__main__':
    main()
