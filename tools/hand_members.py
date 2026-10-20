# -*- coding: utf-8 -*-
"""Attach line-ups found by reading, for bands no database could answer.

MusicBrainz and Discogs between them left 1,407 bands with no line-up, and for most of
those the data simply is not in a database. These came from Bandcamp about-text, band
sites, label pages, interviews and local press, one band at a time.

Unlike Discogs, this source carries instruments, so these members arrive complete.

Every line-up keeps the URL it came from and how confident the reader was:
  high    a page the band controls said it
  medium  a reputable third party said it
  low     pieced together, or knowingly partial
Low-confidence line-ups are published with the doubt written onto the band.
"""
import json, os, re, sys, glob, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = '/home/claude/fest2/work/hand/result_*.json'

def nkey(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and '); s = re.sub(r'^(the|a)\s+', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)

def main():
    found = {}
    for p in sorted(glob.glob(SRC)):
        for r in json.load(open(p, encoding='utf-8')):
            if r.get('members'):
                found[nkey(r['name'])] = r
    if not found:
        print('no hand-research results yet'); return

    filled = people = flagged = 0
    for fid in IDS:
        path = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        for b in d['bands']:
            if b.get('members'):
                continue                 # a database line-up carries years; keep it
            r = found.get(nkey(b['name']))
            if not r:
                continue
            b['members'] = [{'name': m['name'], 'roles': [m['instrument']] if m.get('instrument') else [],
                             'instrument': m.get('instrument', ''), 'instruments': [],
                             'member_attrs': [], 'begin': '', 'end': '',
                             'current': True, 'source': 'Read from ' + (r.get('source') or 'a published source')}
                            for m in r['members']]
            b['member_names'] = ', '.join(m['name'] for m in b['members'])
            b['member_count'] = len(b['members'])
            b['member_source'] = {'high': 'The band’s own page',
                                  'medium': 'Press or label page',
                                  'low': 'Pieced together — treat as partial'}.get(
                                      r.get('confidence'), 'Read from a published source')
            b['member_source_url'] = r.get('source') or ''
            # Only genuinely shaky line-ups get a flag. Flagging every one of them,
            # including the ones read off the band's own page, would make the flag
            # meaningless - which is exactly what the first run did.
            if r.get('note'):
                b['member_note'] = r['note']
            if r.get('confidence') == 'low':
                note = ('Line-up pieced together from a single source and may be partial '
                        'or out of date.')
                if note not in (b.get('flags') or ''):
                    b['flags'] = ((b.get('flags') or '') + ' ' + note).strip()
                    flagged += 1
            filled += 1
            people += len(b['members'])
        json.dump(d, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('hand-researched line-ups attached to %d bands (%d people); %d carry a caveat'
          % (filled, people, flagged))

if __name__ == '__main__':
    main()
